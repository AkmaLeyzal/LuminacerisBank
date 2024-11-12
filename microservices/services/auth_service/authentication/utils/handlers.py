# authentication/utils/handlers.py

import logging
import os
from logging.handlers import RotatingFileHandler

class SafeFileHandler(RotatingFileHandler):
    """Safe file handler that creates directory if not exists"""
    
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=False):
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Initialize the handler
        RotatingFileHandler.__init__(
            self,
            filename,
            mode,
            maxBytes,
            backupCount,
            encoding,
            delay
        )