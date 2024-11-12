# authentication/events/consumer_manager.py
from threading import Thread
import logging
from django.conf import settings
from kafka_cloud.consumer import KafkaConsumer
from kafka_cloud.topics import KafkaTopics
from ..models import User
from ..services import SecurityService

logger = logging.getLogger(__name__)

class ConsumerManager:
    def __init__(self):
        self.consumers = []
        self._initialize_consumers()

    def _initialize_consumers(self):
        """Initialize all Kafka consumers"""
        # Security events consumer
        security_consumer = KafkaConsumer(
            group_id='auth_security_group',
            topics=[
                KafkaTopics.SECURITY_EVENTS,
                KafkaTopics.SUSPICIOUS_ACTIVITIES
            ]
        )
        self.consumers.append(
            (security_consumer, self._handle_security_event)
        )

    def _handle_security_event(self, data: dict, metadata: dict):
        """Handle security-related events"""
        try:
            event_type = data.get('event_type')
            user_id = data.get('user_id')
            
            if not all([event_type, user_id]):
                logger.error("Invalid security event data")
                return

            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.error(f"User not found for security event: {user_id}")
                return

            if event_type == 'SUSPICIOUS_LOGIN':
                SecurityService.handle_suspicious_login(user, data)
            elif event_type == 'MULTIPLE_FAILED_ATTEMPTS':
                SecurityService.handle_failed_attempts(user, data)
            elif event_type == 'FRAUD_DETECTED':
                SecurityService.handle_fraud_detection(user, data)
            else:
                logger.warning(f"Unknown security event type: {event_type}")

        except Exception as e:
            logger.error(f"Error handling security event: {str(e)}")

    def start(self):
        """Start all consumers in separate threads"""
        for consumer, handler in self.consumers:
            thread = Thread(target=self._run_consumer, args=(consumer, handler))
            thread.daemon = True
            thread.start()

    def _run_consumer(self, consumer: KafkaConsumer, handler):
        """Run individual consumer"""
        try:
            consumer.consume(handler)
        except Exception as e:
            logger.error(f"Consumer error: {str(e)}")

    def stop(self):
        """Stop all consumers"""
        for consumer, _ in self.consumers:
            try:
                consumer.stop()
            except Exception as e:
                logger.error(f"Error stopping consumer: {str(e)}")
