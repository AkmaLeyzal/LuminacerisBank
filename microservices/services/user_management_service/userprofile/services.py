# services.py
import requests
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from kafka_cloud.producer import KafkaProducer
from kafka_cloud.topics import KafkaTopics
import logging
from .models import UserProfile, UserDocument

logger = logging.getLogger(__name__)

class UserProfileService:
    def __init__(self):
        self.kafka_producer = KafkaProducer()

    def validate_user_exists(self, user_id):
        """Validate user exists in Auth Service"""
        try:
            # Make request to Auth Service
            response = requests.get(
                f"http://localhost:8001/api/users/{user_id}/",
                headers=self._get_service_headers()
            )
            
            if response.status_code == 404:
                raise ValidationError("User does not exist in Auth Service")
            response.raise_for_status()
            
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error validating user with Auth Service: {str(e)}")
            raise ValidationError("Unable to validate user with Auth Service")

    def create_user_profile(self, user_id, profile_data):
        """Create user profile after validating with Auth Service"""
        # First validate user exists
        auth_user = self.validate_user_exists(user_id)
        
        try:
            # Create profile
            profile = UserProfile.objects.create(
                user_id=user_id,
                **profile_data
            )

            # Publish event to Kafka
            self._publish_profile_event('PROFILE_CREATED', profile)

            return profile

        except Exception as e:
            logger.error(f"Error creating profile for user {user_id}: {str(e)}")
            raise

    def _get_service_headers(self):
        """Get headers for service-to-service communication"""
        return {
            'X-Service-Name': 'user_management_service',
            'X-Service-Token': settings.SERVICE_TOKEN,
        }

    def _publish_profile_event(self, event_type, profile):
        """Publish profile-related event to Kafka"""
        try:
            self.kafka_producer.produce(
                topic=KafkaTopics.USER_EVENTS,
                key=str(profile.user_id),
                value={
                    'event_type': event_type,
                    'profile_id': profile.profile_id,
                    'user_id': profile.user_id,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error publishing Kafka event: {str(e)}")