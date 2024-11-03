# LuminacerisBank/kafka/producer.py
from confluent_kafka import Producer
from .config import KafkaConfig
import json
import logging

logger = logging.getLogger(__name__)

class KafkaProducer:
    def __init__(self):
        self.producer = Producer(KafkaConfig.get_config())

    def produce(self, topic: str, value: dict, key: str = None):
        try:
            self.producer.produce(
                topic=topic,
                key=key.encode('utf-8') if key else None,
                value=json.dumps(value).encode('utf-8'),
                callback=self._delivery_report
            )
            self.producer.flush()
        except Exception as e:
            logger.error(f'Error producing message: {str(e)}')
            raise

    def _delivery_report(self, err, msg):
        if err is not None:
            logger.error(f'Message delivery failed: {err}')
        else:
            logger.debug(f'Message delivered to {msg.topic()} [{msg.partition()}]')