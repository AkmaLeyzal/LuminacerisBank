# authentication/kafka_handlers.py
from kafka_cloud.consumer import KafkaConsumer
from kafka_cloud.producer import KafkaProducer
from kafka_cloud.topics import KafkaTopics
import logging

logger = logging.getLogger(__name__)

class SecurityEventHandler:
    def __init__(self):
        # Try to create topic first
        try:
            producer = KafkaProducer()
            producer.create_topics([KafkaTopics.SECURITY_EVENTS])
        except Exception as e:
            logger.warning(f"Could not create Kafka topic: {str(e)}")

        self.consumer = KafkaConsumer(
            group_id='auth_security_group',
            topics=[KafkaTopics.SECURITY_EVENTS],
            error_handler=self.handle_error
        )

    def handle_error(self, error):
        logger.error(f"Kafka error: {str(error)}")
        # Don't raise exception, just log it
        return True  # Continue processing

    def start_consuming(self):
        """Start consuming security events"""
        try:
            logger.info("Starting security event consumer...")
            self.consumer.consume_messages(self.handle_security_event)
        except Exception as e:
            logger.error(f"Error in security event consumer: {str(e)}")

    def handle_security_event(self, event_data):
        """Handle incoming security events"""
        try:
            logger.info(f"Processing security event: {event_data}")
            # Implementation of event handling
            pass
        except Exception as e:
            logger.error(f"Error handling security event: {str(e)}")