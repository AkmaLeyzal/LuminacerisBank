# authentication/utils/formatters.py
import json
from datetime import datetime
import logging

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for logging"""
    
    def format(self, record):
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
            'module': record.module,
            'process': record.process,
            'thread': record.thread,
        }

        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id

        if record.exc_info:
            log_data['exc_info'] = self.formatException(record.exc_info)

        if hasattr(record, 'extra'):
            log_data.update(record.extra)

        return json.dumps(log_data)
