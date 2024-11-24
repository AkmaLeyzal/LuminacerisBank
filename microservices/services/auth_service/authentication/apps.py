# authentication/apps.py
from django.apps import AppConfig
import sys

class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'
    
    def ready(self):
        if 'runserver' in sys.argv:
            try:
                from .events.consumer_manager import ConsumerManager
                consumer_manager = ConsumerManager()
                consumer_manager.start()
            except Exception as e:
                print(f"Failed to start Kafka consumers: {e}")