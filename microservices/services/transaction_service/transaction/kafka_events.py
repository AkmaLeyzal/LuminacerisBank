# microservices/services/transaction_service/transaction/kafka_events.py
from kafka.producer import KafkaProducer
from kafka.consumer import KafkaConsumer
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class TransactionKafkaEvents:
    def __init__(self):
        self.producer = KafkaProducer()

    def publish_transaction(self, transaction_data: dict):
        """Publish transaction event"""
        try:
            self.producer.produce(
                'TRANSACTIONS',
                {
                    'event_type': 'TRANSACTION_INITIATED',
                    'data': {
                        'transaction_id': str(transaction_data['id']),
                        'user_id': transaction_data['user_id'],
                        'amount': str(transaction_data['amount']),
                        'type': transaction_data['type'],
                        'timestamp': str(datetime.now())
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error publishing transaction: {str(e)}")

    def publish_transaction_completed(self, transaction_data: dict):
        """Publish transaction completion"""
        try:
            self.producer.produce(
                'TRANSACTIONS',
                {
                    'event_type': 'TRANSACTION_COMPLETED',
                    'data': {
                        'transaction_id': str(transaction_data['id']),
                        'status': 'completed',
                        'timestamp': str(datetime.now())
                    }
                }
            )
            
            # Also publish notification
            self.producer.produce(
                'NOTIFICATIONS',
                {
                    'event_type': 'TRANSACTION_NOTIFICATION',
                    'data': {
                        'user_id': transaction_data['user_id'],
                        'message': f"Transaction of {transaction_data['amount']} completed successfully",
                        'timestamp': str(datetime.now())
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error publishing completion: {str(e)}")
