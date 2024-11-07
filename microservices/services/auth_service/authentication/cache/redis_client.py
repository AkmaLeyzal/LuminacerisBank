# authentication/cache/redis_client.py
from django.core.cache import cache
from django.conf import settings
from redis.exceptions import RedisError
from functools import wraps
import json
import logging
from .circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

class RedisClient:
    """Enhanced Redis client with circuit breaker and fallback mechanisms"""

    def __init__(self):
        self.local_cache = {}
        self.circuit_breaker = CircuitBreaker('redis_client')

    @CircuitBreaker('redis_client')
    def get(self, key, default=None):
        """Get value from Redis with local cache fallback"""
        try:
            value = cache.get(key)
            if value is not None:
                self.local_cache[key] = value
                return value

            return self.local_cache.get(key, default)
        except RedisError as e:
            logger.error(f'Redis get error for key {key}: {str(e)}')
            return self.local_cache.get(key, default)

    @CircuitBreaker('redis_client')
    def set(self, key, value, timeout=None):
        """Set value in Redis and local cache"""
        try:
            cache.set(key, value, timeout=timeout)
            self.local_cache[key] = value
            return True
        except RedisError as e:
            logger.error(f'Redis set error for key {key}: {str(e)}')
            self.local_cache[key] = value
            return False

    @CircuitBreaker('redis_client')
    def delete(self, key):
        """Delete value from Redis and local cache"""
        try:
            cache.delete(key)
            self.local_cache.pop(key, None)
            return True
        except RedisError as e:
            logger.error(f'Redis delete error for key {key}: {str(e)}')
            self.local_cache.pop(key, None)
            return False

    @CircuitBreaker('redis_client')
    def incr(self, key):
        """Increment value in Redis with local fallback"""
        try:
            return cache.incr(key)
        except RedisError as e:
            logger.error(f'Redis incr error for key {key}: {str(e)}')
            value = self.local_cache.get(key, 0) + 1
            self.local_cache[key] = value
            return value

    def pipeline_execute(self, operations):
        """Execute multiple operations in a pipeline"""
        try:
            with cache.pipeline() as pipe:
                for op in operations:
                    method = getattr(pipe, op['command'])
                    method(*op.get('args', []), **op.get('kwargs', {}))
                return pipe.execute()
        except RedisError as e:
            logger.error(f'Redis pipeline error: {str(e)}')
            return None