# microservices/services/auth_service/authentication/management/commands/run_kafka_consumer.py
from django.core.management.base import BaseCommand
from authentication.kafka_events import AuthKafkaEvents
import signal
import sys

class Command(BaseCommand):
    help = 'Run Kafka consumer for Auth Service'

    def __init__(self):
        super().__init__()
        self.kafka_events = None

    def handle_shutdown(self, signum, frame):
        self.stdout.write('Shutting down consumer...')
        if self.kafka_events and self.kafka_events.consumer:
            self.kafka_events.consumer.close()
        sys.exit(0)

    def handle(self, *args, **options):
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)

        self.stdout.write('Starting Auth Service Kafka consumer...')
        self.kafka_events = AuthKafkaEvents()
        
        try:
            self.kafka_events.consumer.consume_messages(
                self.kafka_events.handle_fraud_alert
            )
        except KeyboardInterrupt:
            self.handle_shutdown(None, None)