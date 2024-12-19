# notification/kafka_consumer.py
from confluent_kafka import Consumer, KafkaError
from django.conf import settings
import json
import logging
from .services import NotificationService

logger = logging.getLogger(__name__)

class NotificationConsumer:
    def __init__(self):
        self.consumer = Consumer({
            'bootstrap.servers': settings.KAFKA_SETTINGS['BOOTSTRAP_SERVERS'],
            'security.protocol': settings.KAFKA_SETTINGS['SECURITY_PROTOCOL'],
            'sasl.mechanisms': settings.KAFKA_SETTINGS['SASL_MECHANISMS'],
            'sasl.username': settings.KAFKA_SETTINGS['SASL_USERNAME'],
            'sasl.password': settings.KAFKA_SETTINGS['SASL_PASSWORD'],
            'group.id': 'notification_service',
            'auto.offset.reset': 'latest'
        })
        
        self.notification_service = NotificationService()
        self.topics = [
            'transaction-events',
            'security-events',
            'account-events',
            'payment-events',
            'loan-events'
        ]
        self.consumer.subscribe(self.topics)

    def start_consuming(self):
        """Start consuming messages from Kafka"""
        try:
            while True:
                msg = self.consumer.poll(1.0)

                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.info('Reached end of partition')
                        continue
                    logger.error(f'Error in Kafka consumer: {msg.error()}')
                    continue

                try:
                    # Process message
                    topic = msg.topic()
                    value = json.loads(msg.value().decode('utf-8'))
                    
                    logger.info(f'Received message from topic {topic}: {value}')
                    self._process_message(topic, value)

                except json.JSONDecodeError as e:
                    logger.error(f'Error decoding message: {str(e)}')
                except Exception as e:
                    logger.error(f'Error processing message: {str(e)}')

        except KeyboardInterrupt:
            logger.info('Stopping consumer...')
        finally:
            self.consumer.close()

    def _process_message(self, topic: str, message: dict):
        """Process message based on topic and event type"""
        try:
            event_type = message.get('event_type')
            user_id = message.get('user_id')

            if not user_id:
                logger.error(f'No user_id in message: {message}')
                return

            if topic == 'transaction-events':
                self._handle_transaction_event(event_type, message)
            elif topic == 'security-events':
                self._handle_security_event(event_type, message)
            elif topic == 'account-events':
                self._handle_account_event(event_type, message)
            elif topic == 'payment-events':
                self._handle_payment_event(event_type, message)
            elif topic == 'loan-events':
                self._handle_loan_event(event_type, message)

        except Exception as e:
            logger.error(f'Error in message processing: {str(e)}')

    def _handle_transaction_event(self, event_type: str, message: dict):
        """Handle transaction-related events"""
        templates = {
            'TRANSACTION_COMPLETED': {
                'name': 'transaction_success',
                'type': 'TRANSACTION',
                'priority': 'HIGH'
            },
            'TRANSACTION_FAILED': {
                'name': 'transaction_failed',
                'type': 'TRANSACTION',
                'priority': 'HIGH'
            },
            'TRANSACTION_REVERSED': {
                'name': 'transaction_reversed',
                'type': 'TRANSACTION',
                'priority': 'HIGH'
            }
        }

        if template_config := templates.get(event_type):
            amount = message.get('amount', '0')
            currency = message.get('currency', 'IDR')

            self.notification_service.create_notification(
                user_id=message['user_id'],
                notification_data={
                    'template_name': template_config['name'],
                    'type': template_config['type'],
                    'priority': template_config['priority'],
                    'title': f'Transaction {event_type.lower().replace("_", " ")}',
                    'metadata': {
                        'amount': amount,
                        'currency': currency,
                        'transaction_id': message.get('transaction_id'),
                        'reference_number': message.get('reference_number')
                    },
                    'reference_id': message.get('transaction_id'),
                    'reference_type': 'TRANSACTION'
                }
            )

    def _handle_security_event(self, event_type: str, message: dict):
        """Handle security-related events"""
        templates = {
            'LOGIN_ATTEMPT': {
                'name': 'login_attempt',
                'type': 'SECURITY',
                'priority': 'HIGH'
            },
            'PASSWORD_CHANGED': {
                'name': 'password_changed',
                'type': 'SECURITY',
                'priority': 'HIGH'
            },
            'SUSPICIOUS_ACTIVITY': {
                'name': 'suspicious_activity',
                'type': 'SECURITY',
                'priority': 'CRITICAL'
            }
        }

        if template_config := templates.get(event_type):
            self.notification_service.create_notification(
                user_id=message['user_id'],
                notification_data={
                    'template_name': template_config['name'],
                    'type': template_config['type'],
                    'priority': template_config['priority'],
                    'title': f'Security Alert: {event_type.lower().replace("_", " ")}',
                    'metadata': {
                        'ip_address': message.get('ip_address'),
                        'device_info': message.get('device_info'),
                        'location': message.get('location')
                    }
                }
            )

    def _handle_account_event(self, event_type: str, message: dict):
        """Handle account-related events"""
        templates = {
            'BALANCE_LOW': {
                'name': 'balance_low',
                'type': 'ACCOUNT',
                'priority': 'MEDIUM'
            },
            'ACCOUNT_LOCKED': {
                'name': 'account_locked',
                'type': 'ACCOUNT',
                'priority': 'HIGH'
            }
        }

        if template_config := templates.get(event_type):
            self.notification_service.create_notification(
                user_id=message['user_id'],
                notification_data={
                    'template_name': template_config['name'],
                    'type': template_config['type'],
                    'priority': template_config['priority'],
                    'title': f'Account Alert: {event_type.lower().replace("_", " ")}',
                    'metadata': message
                }
            )

    def _handle_payment_event(self, event_type: str, message: dict):
        """Handle payment-related events"""
        templates = {
            'PAYMENT_DUE': {
                'name': 'payment_due',
                'type': 'PAYMENT',
                'priority': 'MEDIUM'
            },
            'PAYMENT_RECEIVED': {
                'name': 'payment_received',
                'type': 'PAYMENT',
                'priority': 'MEDIUM'
            }
        }

        if template_config := templates.get(event_type):
            self.notification_service.create_notification(
                user_id=message['user_id'],
                notification_data={
                    'template_name': template_config['name'],
                    'type': template_config['type'],
                    'priority': template_config['priority'],
                    'title': f'Payment Update: {event_type.lower().replace("_", " ")}',
                    'metadata': {
                        'amount': message.get('amount'),
                        'currency': message.get('currency'),
                        'payment_id': message.get('payment_id'),
                        'due_date': message.get('due_date')
                    }
                }
            )

    def _handle_loan_event(self, event_type: str, message: dict):
        """Handle loan-related events"""
        templates = {
            'LOAN_APPROVED': {
                'name': 'loan_approved',
                'type': 'LOAN',
                'priority': 'HIGH'
            },
            'LOAN_REJECTED': {
                'name': 'loan_rejected',
                'type': 'LOAN',
                'priority': 'HIGH'
            },
            'LOAN_PAYMENT_DUE': {
                'name': 'loan_payment_due',
                'type': 'LOAN',
                'priority': 'MEDIUM'
            }
        }

        if template_config := templates.get(event_type):
            self.notification_service.create_notification(
                user_id=message['user_id'],
                notification_data={
                    'template_name': template_config['name'],
                    'type': template_config['type'],
                    'priority': template_config['priority'],
                    'title': f'Loan Update: {event_type.lower().replace("_", " ")}',
                    'metadata': {
                        'loan_id': message.get('loan_id'),
                        'amount': message.get('amount'),
                        'currency': message.get('currency'),
                        'interest_rate': message.get('interest_rate'),
                        'term_months': message.get('term_months')
                    }
                }
            )