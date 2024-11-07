# authentication/cache/circuit_breaker.py
from functools import wraps
from datetime import datetime, timedelta
import threading
import logging
from django.core.cache import cache
from django.conf import settings
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

class CircuitBreaker:
    """Circuit breaker implementation for Redis operations"""
    
    def __init__(self, name, failure_threshold=5, reset_timeout=60):
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure = None
        self.state = 'closed'  # closed, open, or half-open
        self._lock = threading.Lock()

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == 'open':
                if self._should_attempt_reset():
                    self._enter_half_open_state()
                else:
                    raise RedisError('Circuit breaker is open')

            try:
                result = func(*args, **kwargs)
                self._handle_success()
                return result
            except RedisError as e:
                self._handle_failure(e)
                raise

        return wrapper

    def _should_attempt_reset(self):
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure:
            return True
        return (datetime.utcnow() - self.last_failure).seconds >= self.reset_timeout

    def _enter_half_open_state(self):
        """Enter half-open state to test if service is recovered"""
        with self._lock:
            self.state = 'half-open'
            logger.info(f'Circuit breaker {self.name} entering half-open state')

    def _handle_success(self):
        """Handle successful operation"""
        with self._lock:
            if self.state != 'closed':
                self.state = 'closed'
                self.failures = 0
                self.last_failure = None
                logger.info(f'Circuit breaker {self.name} closed')

    def _handle_failure(self, exception):
        """Handle failed operation"""
        with self._lock:
            self.failures += 1
            self.last_failure = datetime.utcnow()
            
            if self.failures >= self.failure_threshold:
                self.state = 'open'
                logger.warning(
                    f'Circuit breaker {self.name} opened after {self.failures} failures'
                )
