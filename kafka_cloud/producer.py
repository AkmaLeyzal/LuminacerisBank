# kafka_cloud/producer.py

from confluent_kafka import Producer
from .config import KafkaConfig
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class KafkaProducer:
    def __init__(self):
        self.producer = Producer(KafkaConfig.get_config())
        self._ensure_topics_exist()

    def _ensure_topics_exist(self):
        """Ensure all required topics exist"""
        # Implementation depends on your Kafka setup
        pass

    def produce(self, topic: str, value: Dict, key: Optional[str] = None, headers: Optional[Dict] = None) -> bool:
        """Produce message to Kafka topic"""
        try:
            # Convert value to JSON string
            value_json = json.dumps(value)
            
            # Prepare headers if provided
            kafka_headers = [(k, str(v).encode('utf-8')) for k, v in (headers or {}).items()]

            # Produce message
            self.producer.produce(
                topic=topic,
                key=key.encode('utf-8') if key else None,
                value=value_json.encode('utf-8'),
                headers=kafka_headers if kafka_headers else None,
                on_delivery=self._delivery_callback
            )

            # Flush producer
            self.producer.flush()
            return True

        except Exception as e:
            logger.error(f"Failed to produce message to {topic}: {str(e)}")
            return False

    def _delivery_callback(self, err, msg):
        """Callback for message delivery reports"""
        if err:
            logger.error(f'Message delivery failed: {str(err)}')
        else:
            logger.debug(f'Message delivered to {msg.topic()} [{msg.partition()}] @ {msg.offset()}')
