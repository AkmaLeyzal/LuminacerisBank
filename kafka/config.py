# kafka/config.py
from typing import Dict
from django.conf import settings
import os

class KafkaConfig:
    TOPICS = {
        'TRANSACTIONS': 'transactions',
        'NOTIFICATIONS': 'notifications',
        'FRAUD_ALERTS': 'fraud-alerts',
        'USER_EVENTS': 'user-events',
        'AUDIT_LOGS': 'audit-logs'
    }

    @staticmethod
    def get_config() -> Dict:
        return {
            'bootstrap.servers': os.getenv('CONFLUENT_BOOTSTRAP_SERVERS'),
            'security.protocol': 'SASL_SSL',
            'sasl.mechanisms': 'PLAIN',
            'sasl.username': os.getenv('CONFLUENT_SASL_USERNAME'),
            'sasl.password': os.getenv('CONFLUENT_SASL_PASSWORD'),
            'session.timeout.ms': 45000,
            'client.id': os.getenv('CONFLUENT_CLIENT_ID')
        }
