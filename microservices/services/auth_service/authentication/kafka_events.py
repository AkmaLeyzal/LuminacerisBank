# microservices/services/auth_service/authentication/kafka_events.py
from kafka_cloud.producer import KafkaProducer
from kafka_cloud.consumer import KafkaConsumer
from django.conf import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AuthKafkaEvents:
    def __init__(self):
        self.producer = KafkaProducer()
        self.consumer = KafkaConsumer(
            group_id='auth_service',
            topics=['FRAUD_ALERTS']
        )

    def publish_login_event(self, user_id: int, status: str, ip_address: str):
        """Publish login events"""
        try:
            self.producer.produce(
                'USER_EVENTS',
                {
                    'event_type': 'USER_LOGIN',
                    'data': {
                        'user_id': user_id,
                        'status': status,
                        'ip_address': ip_address,
                        'timestamp': str(datetime.now())
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error publishing login event: {str(e)}")

    async def blacklist_user_tokens(self, user_id: int):
        """Blacklist user tokens"""
        try:
            from django.core.cache import cache
            cache_key = f"token_blacklist:user:{user_id}"
            await cache.set(cache_key, True, timeout=24*60*60)  # 24 hours
        except Exception as e:
            logger.error(f"Error blacklisting tokens: {str(e)}")

    async def handle_fraud_alert(self, message: dict):
        """Handle fraud alerts"""
        try:
            if message['event_type'] == 'FRAUD_DETECTED':
                user_id = message['data']['user_id']
                # Implement token blacklist
                await self.blacklist_user_tokens(user_id)
                # Publish to audit log
                self.producer.produce(
                    'AUDIT_LOGS',
                    {
                        'event_type': 'USER_BLOCKED',
                        'data': {
                            'user_id': user_id,
                            'reason': 'fraud_detected',
                            'timestamp': str(datetime.now())
                        }
                    }
                )
        except Exception as e:
            logger.error(f"Error handling fraud alert: {str(e)}")

    async def start_consumer(self):
        """Start consuming fraud alerts"""
        try:
            while True:
                message = await self.consumer.get_message()
                if message:
                    await self.handle_fraud_alert(message)
        except Exception as e:
            logger.error(f"Error in consumer: {str(e)}")