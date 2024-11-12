# authentication/utils/formatters.py

import json
import logging
import traceback
from datetime import datetime
from django.utils import timezone

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for logging"""
    
    def format(self, record):
        """Format log record as JSON"""
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        
        log_data = {
            'timestamp': timestamp,
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'path': record.pathname,
            'line_number': record.lineno,
            'logger': record.name
        }
        
        # Add exception info if exists
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'stacktrace': traceback.format_exception(*record.exc_info)
            }
            
        # Add extra fields if any
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
            
        return json.dumps(log_data)