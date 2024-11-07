# authentication/utils/logging.py
import logging
import json
import threading
from functools import wraps
from datetime import datetime
from django.conf import settings
from kafka_cloud.producer import KafkaProducer

logger = logging.getLogger(__name__)
kafka_producer = KafkaProducer()

class CustomLogger:
    @staticmethod
    def format_log(level, message, extra=None):
        """Format log message with additional context"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'message': message,
            'service': 'auth_service',
            'thread_id': threading.get_ident(),
        }
        
        if extra:
            log_data.update(extra)
            
        return json.dumps(log_data)

    @staticmethod
    def error(message, exc_info=None, extra=None):
        """Log error message"""
        logger.error(
            CustomLogger.format_log('ERROR', message, extra),
            exc_info=exc_info
        )
        
        # Send error to Kafka for centralized logging
        try:
            kafka_producer.produce(
                topic='error-logs',
                value={
                    'service': 'auth_service',
                    'level': 'ERROR',
                    'message': message,
                    'timestamp': datetime.utcnow().isoformat(),
                    'extra': extra
                }
            )
        except Exception as e:
            logger.error(f"Failed to send error to Kafka: {str(e)}")

    @staticmethod
    def warning(message, extra=None):
        """Log warning message"""
        logger.warning(
            CustomLogger.format_log('WARNING', message, extra)
        )

    @staticmethod
    def info(message, extra=None):
        """Log info message"""
        logger.info(
            CustomLogger.format_log('INFO', message, extra)
        )

    @staticmethod
    def debug(message, extra=None):
        """Log debug message"""
        logger.debug(
            CustomLogger.format_log('DEBUG', message, extra)
        )
