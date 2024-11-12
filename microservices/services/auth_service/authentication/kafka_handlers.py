# authentication/kafka_handlers.py

from kafka_cloud.consumer import KafkaConsumer
from kafka_cloud.topics import KafkaTopics
from .services import SecurityService
from .models import User
import logging

logger = logging.getLogger(__name__)

class AuthKafkaHandler:
    def __init__(self):
        self.security_consumer = KafkaConsumer(
            group_id='auth_security_group',
            topics=[
                KafkaTopics.SECURITY_EVENTS,
                KafkaTopics.SUSPICIOUS_ACTIVITIES
            ]
        )

    def handle_security_event(self, data: dict, metadata: dict):
        """Handle security-related events"""
        try:
            event_type = data.get('event_type')
            user_id = data.get('user_id')
            
            if not all([event_type, user_id]):
                logger.error("Invalid security event data")
                return

            user = User.objects.get(id=user_id)
            
            if event_type == 'SUSPICIOUS_LOGIN':
                SecurityService.handle_suspicious_login(user, data)
            elif event_type == 'MULTIPLE_FAILED_ATTEMPTS':
                SecurityService.handle_failed_attempts(user, data)
            elif event_type == 'FRAUD_DETECTED':
                SecurityService.handle_fraud_detection(user, data)
            else:
                logger.warning(f"Unknown security event type: {event_type}")

        except User.DoesNotExist:
            logger.error(f"User not found for security event: {user_id}")
        except Exception as e:
            logger.error(f"Error handling security event: {str(e)}")

    def start(self):
        """Start consuming messages"""
        try:
            self.security_consumer.consume(self.handle_security_event)
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {str(e)}")

    def stop(self):
        """Stop consuming messages"""
        self.security_consumer.stop()