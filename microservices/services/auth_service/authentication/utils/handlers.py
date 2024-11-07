import os
import logging
from logging.handlers import RotatingFileHandler

class SafeFileHandler(RotatingFileHandler):
    """File handler that creates directory if it doesn't exist"""
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=False):
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        RotatingFileHandler.__init__(self, filename, mode, maxBytes, backupCount, encoding, delay)
