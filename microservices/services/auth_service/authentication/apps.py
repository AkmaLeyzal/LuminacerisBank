from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'
    
    def ready(self):
        try:
            import sys
            from .events.consumer_manager import ConsumerManager
            if not any([arg.endswith('manage.py') for arg in sys.argv]):
                consumer_manager = ConsumerManager()
                consumer_manager.start()
        except Exception as e:
            logger.error(f"Failed to start Kafka consumers: {str(e)}")