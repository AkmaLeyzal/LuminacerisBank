# microservices/services/fraud_detection_service/fraud_detection/kafka_events.py
from kafka_cloud.producer import KafkaProducer
from kafka_cloud.consumer import KafkaConsumer
import logging

logger = logging.getLogger(__name__)

class FraudDetectionKafkaEvents:
    def __init__(self):
        self.producer = KafkaProducer()
        self.consumer = KafkaConsumer(
            group_id='fraud_detection_service',
            topics=['TRANSACTIONS', 'USER_EVENTS']
        )

    async def handle_transaction(self, message: dict):
        """Handle incoming transactions"""
        try:
            if message['event_type'] == 'TRANSACTION_INITIATED':
                transaction_data = message['data']
                
                # Analyze for fraud
                fraud_score = await self.analyze_transaction(transaction_data)
                
                if fraud_score > 0.7:  # High risk
                    # Publish fraud alert
                    self.producer.produce(
                        'FRAUD_ALERTS',
                        {
                            'event_type': 'FRAUD_DETECTED',
                            'data': {
                                'user_id': transaction_data['user_id'],
                                'transaction_id': transaction_data['transaction_id'],
                                'fraud_score': fraud_score,
                                'timestamp': str(datetime.now())
                            }
                        }
                    )
                    
                    # Publish notification
                    self.producer.produce(
                        'NOTIFICATIONS',
                        {
                            'event_type': 'FRAUD_NOTIFICATION',
                            'data': {
                                'user_id': transaction_data['user_id'],
                                'message': 'Suspicious activity detected on your account',
                                'timestamp': str(datetime.now())
                            }
                        }
                    )
        except Exception as e:
            logger.error(f"Error handling transaction: {str(e)}")

    def start_monitoring(self):
        """Start monitoring transactions"""
        try:
            self.consumer.start(self.handle_transaction)
        except Exception as e:
            logger.error(f"Error starting consumer: {str(e)}")

# Use in management command
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Start Fraud Detection Kafka Consumer'

    def handle(self, *args, **options):
        kafka_events = FraudDetectionKafkaEvents()
        self.stdout.write('Starting Fraud Detection consumer...')
        kafka_events.start_monitoring()