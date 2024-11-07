# authentication/cache/session_cache.py
from .redis_client import RedisClient
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class SessionCache:
    """Session caching with Redis and local fallback"""

    def __init__(self):
        self.redis = RedisClient()
        self.prefix = 'session:'

    def cache_session(self, session_id, session_data, timeout=None):
        """Cache session data"""
        key = f'{self.prefix}{session_id}'
        self.redis.set(
            key,
            json.dumps(session_data),
            timeout=timeout or 86400  # 24 hours default
        )

    def get_session(self, session_id):
        """Get session data"""
        key = f'{self.prefix}{session_id}'
        data = self.redis.get(key)
        return json.loads(data) if data else None

    def update_session_activity(self, session_id):
        """Update session last activity"""
        key = f'{self.prefix}{session_id}'
        data = self.get_session(session_id)
        if data:
            data['last_activity'] = datetime.utcnow().isoformat()
            self.cache_session(session_id, data)

    def end_session(self, session_id):
        """End a session"""
        key = f'{self.prefix}{session_id}'
        user_sessions_key = f'user_sessions:{session_id}'
        
        operations = [
            {'command': 'delete', 'args': [key]},
            {'command': 'delete', 'args': [user_sessions_key]}
        ]
        
        self.redis.pipeline_execute(operations)