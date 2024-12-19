#luminacerisBank/kafka/consumer.py
from confluent_kafka import Consumer, KafkaError
import json
import logging
import uuid
from .config import KafkaConfig

logger = logging.getLogger(__name__)

class KafkaConsumer:
    def __init__(self, group_id: str, topics: list):
        config = KafkaConfig.get_config()
        config.update({
            'group.id': group_id,
            'auto.offset.reset': 'earliest'
        })
        self.consumer = Consumer(config)
        self.consumer.subscribe(topics)
        self.running = True

    def consume_messages(self, handler):
        while self.running:
            try:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    logger.error(f'Consumer error: {msg.error()}')
                    continue

                value = json.loads(msg.value().decode('utf-8'))
                # Process the message with the handler
                handler(value)

            except json.JSONDecodeError as e:
                logger.error(f'Error decoding message: {str(e)}')
            except Exception as e:
                logger.error(f'Error processing message: {str(e)}')