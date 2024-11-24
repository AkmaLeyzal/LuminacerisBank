# authentication/utils/formatters.py

import json
import logging
from datetime import datetime

class JsonFormatter(logging.Formatter):
    def format(self, record):
        """Format log record as JSON"""
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'path': record.pathname,
            'line_number': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)

    def formatTime(self, record):
        """Format timestamp in ISO format"""
        dt = datetime.fromtimestamp(record.created)
        return dt.isoformat()