# kafka/producer.py
from confluent_kafka import Producer
from .config import KafkaConfig
import json
import logging

logger = logging.getLogger(__name__)

class KafkaProducer:
    def __init__(self):
        self.producer = Producer(KafkaConfig.get_config())

    def delivery_callback(self, err, msg):
        if err:
            logger.error(f'Message delivery failed: {err}')
        else:
            logger.info(f'Message delivered to {msg.topic()} [{msg.partition()}]')

    def produce(self, topic: str, message: dict, key: str = None):
        try:
            value = json.dumps(message).encode('utf-8')
            self.producer.produce(
                topic=KafkaConfig.TOPICS.get(topic, topic),
                key=key.encode('utf-8') if key else None,
                value=value,
                callback=self.delivery_callback
            )
            self.producer.flush()
        except Exception as e:
            logger.error(f'Error producing message: {str(e)}')
            raise