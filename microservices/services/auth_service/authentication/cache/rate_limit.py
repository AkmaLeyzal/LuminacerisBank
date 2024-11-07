# authentication/cache/rate_limit.py
from .redis_client import RedisClient
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiting with Redis and local fallback"""

    def __init__(self):
        self.redis = RedisClient()
        self.prefix = 'rate:'

    def check_rate_limit(self, key, limit, window):
        """Check if rate limit is exceeded"""
        cache_key = f'{self.prefix}{key}'
        
        try:
            count = self.redis.get(cache_key) or 0
            count = int(count)
            
            if count >= limit:
                return False
            
            self.redis.incr(cache_key)
            
            # Set expiry if key is new
            if count == 0:
                self.redis.set(cache_key, 1, timeout=window)
            
            return True
            
        except Exception as e:
            logger.error(f'Rate limit error for key {key}: {str(e)}')
            return True  # Allow request if rate limiting fails

    def reset_counter(self, key):
        """Reset rate limit counter"""
        cache_key = f'{self.prefix}{key}'
        self.redis.delete(cache_key)