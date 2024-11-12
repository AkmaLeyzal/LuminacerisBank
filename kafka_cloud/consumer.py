# kafka_cloud/consumer.py

from confluent_kafka import Consumer, KafkaError, OFFSET_BEGINNING
from typing import List, Callable, Dict
import json
import logging
from .config import KafkaConfig

logger = logging.getLogger(__name__)

class KafkaConsumer:
    def __init__(self, group_id: str, topics: List[str], auto_offset_reset: str = 'earliest'):
        """Initialize Kafka consumer"""
        config = KafkaConfig.get_config()
        config.update({
            'group.id': group_id,
            'auto.offset.reset': auto_offset_reset,
            'enable.auto.commit': False  # Manual commit for better control
        })
        
        self.consumer = Consumer(config)
        self.topics = topics
        self.running = False
        self._subscribe_to_topics()

    def _subscribe_to_topics(self):
        """Subscribe to specified topics"""
        try:
            self.consumer.subscribe(
                self.topics,
                on_assign=self._on_assign
            )
        except Exception as e:
            logger.error(f"Failed to subscribe to topics: {str(e)}")
            raise

    def _on_assign(self, consumer, partitions):
        """Callback for partition assignment"""
        for partition in partitions:
            partition.offset = OFFSET_BEGINNING
        
        logger.info(f"Assigned partitions: {partitions}")
        consumer.assign(partitions)

    def consume(self, handler: Callable[[Dict], None], timeout: float = 1.0):
        """Start consuming messages"""
        self.running = True
        
        try:
            while self.running:
                msg = self.consumer.poll(timeout)
                
                if msg is None:
                    continue
                    
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    logger.error(f"Consumer error: {msg.error()}")
                    continue

                try:
                    # Parse message value
                    value = json.loads(msg.value().decode('utf-8'))
                    
                    # Get headers if any
                    headers = {k: v.decode('utf-8') for k, v in msg.headers() or []}
                    
                    # Add message metadata
                    metadata = {
                        'topic': msg.topic(),
                        'partition': msg.partition(),
                        'offset': msg.offset(),
                        'timestamp': msg.timestamp(),
                        'headers': headers
                    }
                    
                    # Process message
                    handler(value, metadata)
                    
                    # Commit offset after successful processing
                    self.consumer.commit(msg)

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode message: {str(e)}")
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")

        except Exception as e:
            logger.error(f"Consumer error: {str(e)}")
        finally:
            self.stop()

    def stop(self):
        """Stop consuming messages"""
        self.running = False
        self.consumer.close()