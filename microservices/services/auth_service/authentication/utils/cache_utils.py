# authentication/utils/cache_utils.py

from django.core.cache import cache
from django.conf import settings
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

class CacheService:
    @staticmethod
    def generate_key(prefix: str, *args) -> str:
        """Generate cache key based on prefix and arguments"""
        return settings.CACHE_KEYS[prefix].format(*args)

    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            return cache.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None

    @staticmethod
    def set(key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """Set value in cache with optional timeout"""
        try:
            cache.set(key, value, timeout=timeout)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False

    @staticmethod
    def delete(key: str) -> bool:
        """Delete value from cache"""
        try:
            cache.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False

    @staticmethod
    def increment(key: str, delta: int = 1) -> Optional[int]:
        """Increment value in cache"""
        try:
            return cache.incr(key, delta)
        except Exception as e:
            logger.error(f"Cache increment error: {str(e)}")
            return None

    @staticmethod
    def set_many(data: dict, timeout: Optional[int] = None) -> bool:
        """Set multiple values in cache"""
        try:
            cache.set_many(data, timeout=timeout)
            return True
        except Exception as e:
            logger.error(f"Cache set_many error: {str(e)}")
            return False

class TokenCache:
    """Handle token-related caching"""
    
    @staticmethod
    def store_token(token_id: str, token_data: dict, expires_in: int) -> bool:
        """Store token data in cache"""
        key = CacheService.generate_key('TOKEN', token_id)
        return CacheService.set(key, token_data, timeout=expires_in)

    @staticmethod
    def get_token(token_id: str) -> Optional[dict]:
        """Get token data from cache"""
        key = CacheService.generate_key('TOKEN', token_id)
        return CacheService.get(key)

    @staticmethod
    def invalidate_token(token_id: str) -> bool:
        """Invalidate token in cache"""
        key = CacheService.generate_key('TOKEN', token_id)
        return CacheService.delete(key)

class SessionCache:
    """Handle session-related caching"""
    
    @staticmethod
    def store_session(session_id: str, session_data: dict, expires_in: int) -> bool:
        """Store session data in cache"""
        key = CacheService.generate_key('USER_SESSION', session_id)
        return CacheService.set(key, session_data, timeout=expires_in)

    @staticmethod
    def get_session(session_id: str) -> Optional[dict]:
        """Get session data from cache"""
        key = CacheService.generate_key('USER_SESSION', session_id)
        return CacheService.get(key)

    @staticmethod
    def invalidate_session(session_id: str) -> bool:
        """Invalidate session in cache"""
        key = CacheService.generate_key('USER_SESSION', session_id)
        return CacheService.delete(key)

class RateLimitCache:
    """Handle rate limiting caching"""
    
    @staticmethod
    def increment_attempts(identifier: str, action: str) -> Optional[int]:
        """Increment attempt count for rate limiting"""
        key = CacheService.generate_key('RATE_LIMIT', action, identifier)
        return CacheService.increment(key)

    @staticmethod
    def get_attempts(identifier: str, action: str) -> int:
        """Get current attempt count"""
        key = CacheService.generate_key('RATE_LIMIT', action, identifier)
        return CacheService.get(key) or 0

    @staticmethod
    def reset_attempts(identifier: str, action: str) -> bool:
        """Reset attempt count"""
        key = CacheService.generate_key('RATE_LIMIT', action, identifier)
        return CacheService.delete(key)