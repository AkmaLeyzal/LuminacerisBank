# authentication/events/consumer_manager.py
import threading
import logging
from .handlers import SecurityEventHandler

logger = logging.getLogger(__name__)

class ConsumerManager:
    """Manage Kafka consumers in separate threads"""
    
    def __init__(self):
        self.security_handler = SecurityEventHandler()
        self.consumers = []

    def start_consumers(self):
        """Start all consumers in separate threads"""
        try:
            # Security events consumer
            security_thread = threading.Thread(
                target=self.security_handler.start_consuming,
                name='security_consumer'
            )
            security_thread.daemon = True
            security_thread.start()
            self.consumers.append(security_thread)

            logger.info("All Kafka consumers started successfully")

        except Exception as e:
            logger.error(f"Error starting consumers: {str(e)}", exc_info=True)
            raise

    def stop_consumers(self):
        """Stop all consumers"""
        try:
            self.security_handler.consumer.close()
            logger.info("All Kafka consumers stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping consumers: {str(e)}", exc_info=True)
