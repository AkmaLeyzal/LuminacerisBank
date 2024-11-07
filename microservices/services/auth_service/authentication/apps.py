# In apps.py
from django.apps import AppConfig

class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'
    
    def ready(self):
        """Start Kafka consumers when the application starts"""
        # Avoid starting consumers in management commands
        import sys
        if ('runserver' in sys.argv or 'uvicorn' in sys.argv) and not any(arg.startswith('--help') for arg in sys.argv):
            from .events.consumer_manager import ConsumerManager
            consumer_manager = ConsumerManager()
            consumer_manager.start_consumers()