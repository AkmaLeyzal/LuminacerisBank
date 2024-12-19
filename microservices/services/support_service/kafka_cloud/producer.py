#luminacerisBank/kafka/producer.py
from confluent_kafka import Producer
from .config import KafkaConfig
import json
import logging
import uuid

logger = logging.getLogger(__name__)

class KafkaProducer:
    def __init__(self):
        self.producer = Producer(KafkaConfig.get_config())

    def produce(self, topic: str, value: dict, key: str = None):
        try:
            # Convert the message to JSON-serializable format
            serializable_value = self._prepare_message(value)
            
            self.producer.produce(
                topic=topic,
                key=key.encode('utf-8') if key else None,
                value=json.dumps(serializable_value).encode('utf-8'),
                callback=self._delivery_report
            )
            self.producer.flush()
        except Exception as e:
            logger.error(f'Error producing message: {str(e)}')
            raise

    def _prepare_message(self, value: dict) -> dict:
        """Prepare message for serialization"""
        def serialize_value(v):
            if isinstance(v, uuid.UUID):
                return str(v)
            elif isinstance(v, dict):
                return {k: serialize_value(v) for k, v in v.items()}
            elif isinstance(v, list):
                return [serialize_value(item) for item in v]
            return v

        return {k: serialize_value(v) for k, v in value.items()}

    def _delivery_report(self, err, msg):
        if err is not None:
            logger.error(f'Message delivery failed: {err}')
        else:
            logger.debug(f'Message delivered to {msg.topic()} [{msg.partition()}]')
