# authentication/events/handlers.py
from django.conf import settings
from django.core.cache import cache
from kafka_cloud.consumer import KafkaConsumer
from kafka_cloud.topics import KafkaTopics
from ..models import User, SecurityAuditLog
import json
import logging

logger = logging.getLogger(__name__)

class SecurityEventHandler:
    def __init__(self):
        self.consumer = KafkaConsumer(
            group_id='auth_security_group',
            topics=[KafkaTopics.SECURITY_EVENTS]
        )

    def handle_security_event(self, event_data):
        """Handle incoming security events"""
        try:
            event_type = event_data.get('event_type')
            user_id = event_data.get('user_id')

            if not all([event_type, user_id]):
                logger.error(f"Invalid event data: {event_data}")
                return

            handler_method = getattr(self, f"handle_{event_type.lower()}", None)
            if handler_method:
                handler_method(event_data)
            else:
                logger.warning(f"No handler for event type: {event_type}")

        except Exception as e:
            logger.error(f"Error handling security event: {str(e)}", exc_info=True)

    def handle_login_failed(self, event_data):
        """Handle failed login attempts"""
        username = event_data.get('username')
        ip_address = event_data.get('ip_address')

        # Update failed attempts counter in Redis
        cache_key = f"failed_login:{username}"
        failed_attempts = cache.get(cache_key) or 0
        
        if failed_attempts >= 5:
            # Auto-block user after 5 failed attempts
            try:
                user = User.objects.get(username=username)
                user.status = User.Status.LOCKED
                user.save()

                # Create security audit log
                SecurityAuditLog.objects.create(
                    user_id=user.id,
                    event_type='ACCOUNT_LOCKED',
                    ip_address=ip_address,
                    details={
                        'reason': 'Multiple failed login attempts',
                        'failed_attempts': failed_attempts + 1
                    }
                )
            except User.DoesNotExist:
                logger.warning(f"User not found: {username}")

    def handle_suspicious_activity(self, event_data):
        """Handle suspicious activity alerts"""
        user_id = event_data.get('user_id')
        risk_score = event_data.get('risk_score', 0)

        if risk_score > 80:
            # High risk - require additional verification
            cache_key = f"user:{user_id}:requires_verification"
            cache.set(cache_key, True, timeout=3600)  # 1 hour

            # Create security audit log
            SecurityAuditLog.objects.create(
                user_id=user_id,
                event_type='HIGH_RISK_ACTIVITY',
                details=event_data
            )

    def start_consuming(self):
        """Start consuming security events"""
        logger.info("Starting security event consumer...")
        self.consumer.consume_messages(self.handle_security_event)

