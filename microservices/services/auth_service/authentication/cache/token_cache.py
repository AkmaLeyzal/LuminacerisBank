# authentication/cache/token_cache.py
from .redis_client import RedisClient
from datetime import datetime, timedelta
import jwt
import json
import logging

logger = logging.getLogger(__name__)

class TokenCache:
    """Token caching with Redis and local fallback"""

    def __init__(self):
        self.redis = RedisClient()
        self.prefix = 'token:'

    def cache_token(self, token_id, payload, token_type='access'):
        """Cache token data"""
        key = f'{self.prefix}{token_id}'
        token_data = {
            'user_id': payload['user_id'],
            'token_type': token_type,
            'exp': payload['exp'],
            'is_blacklisted': False
        }

        timeout = int((datetime.fromtimestamp(payload['exp']) - datetime.utcnow()).total_seconds())
        self.redis.set(key, json.dumps(token_data), timeout=timeout)

    def is_token_valid(self, token_id):
        """Check if token is valid"""
        key = f'{self.prefix}{token_id}'
        token_data = self.redis.get(key)

        if token_data:
            data = json.loads(token_data)
            return not data.get('is_blacklisted', False)
        return False

    def blacklist_token(self, token_id, reason=None):
        """Blacklist a token"""
        key = f'{self.prefix}{token_id}'
        blacklist_key = f'blacklist:{token_id}'

        operations = [
            {
                'command': 'set',
                'args': [blacklist_key, 'blacklisted'],
                'kwargs': {'timeout': 86400}  # 24 hours
            }
        ]

        token_data = self.redis.get(key)
        if token_data:
            data = json.loads(token_data)
            data['is_blacklisted'] = True
            data['blacklist_reason'] = reason
            operations.append({
                'command': 'set',
                'args': [key, json.dumps(data)],
                'kwargs': {'timeout': int((datetime.fromtimestamp(data['exp']) - datetime.utcnow()).total_seconds())}
            })

        self.redis.pipeline_execute(operations)
