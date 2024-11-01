# auth_service/authentication/utils/redis_utils.py

from django.core.cache import cache
from django.conf import settings
import json
from datetime import datetime, timedelta

class RedisService:
    @staticmethod
    def set_token_data(token_id: str, payload: dict, expiry: int = None):
        """Store token data in Redis"""
        key = settings.CACHE_KEYS['TOKEN'].format(token_id)
        if not expiry:
            expiry = settings.CACHE_TTL
        
        try:
            cache.set(key, json.dumps(payload), timeout=expiry)
            return True
        except Exception as e:
            print(f"Redis error: {str(e)}")
            return False

    @staticmethod
    def get_token_data(token_id: str):
        """Retrieve token data from Redis"""
        key = settings.CACHE_KEYS['TOKEN'].format(token_id)
        try:
            data = cache.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            print(f"Redis error: {str(e)}")
            return None

    @staticmethod
    def check_rate_limit(key_prefix: str, identifier: str) -> bool:
        """Check rate limit for given identifier"""
        key = settings.CACHE_KEYS['RATE_LIMIT'].format(key_prefix, identifier)
        try:
            attempts = cache.get(key, 0)
            limit = settings.RATE_LIMIT[key_prefix]['ATTEMPTS']
            return int(attempts) < limit
        except Exception as e:
            print(f"Redis error: {str(e)}")
            return True  # Allow on error

    @staticmethod
    def increment_rate_limit(key_prefix: str, identifier: str):
        """Increment rate limit counter"""
        key = settings.CACHE_KEYS['RATE_LIMIT'].format(key_prefix, identifier)
        try:
            pipe = cache.client.pipeline()
            pipe.incr(key)
            pipe.expire(key, settings.RATE_LIMIT[key_prefix]['WINDOW'])
            pipe.execute()
        except Exception as e:
            print(f"Redis error: {str(e)}")

    @staticmethod
    def cleanup_expired_data():
        """Cleanup expired tokens and sessions"""
        try:
            # Redis cloud akan handle ini otomatis dengan maxmemory-policy
            pass
        except Exception as e:
            print(f"Redis error: {str(e)}")