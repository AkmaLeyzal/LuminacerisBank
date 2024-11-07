# authentication/services/security_service.py
from django.core.cache import cache
from datetime import datetime, timedelta
from authentication.models import UserSession
import hashlib
import json

class SecurityService:
    @staticmethod
    def check_rate_limit(key, limit, window):
        """Check rate limiting using Redis"""
        cache_key = f'rate:{key}'
        
        # Get current count
        count = cache.get(cache_key) or 0
        
        if count >= limit:
            return False
        
        # Increment counter
        pipe = cache.client.pipeline()
        pipe.incr(cache_key)
        pipe.expire(cache_key, window)
        pipe.execute()
        
        return True

    @staticmethod
    def generate_device_id(request_data):
        """Generate unique device identifier"""
        device_data = {
            'user_agent': request_data.get('user_agent', ''),
            'ip': request_data.get('ip', ''),
            'platform': request_data.get('platform', ''),
            'browser': request_data.get('browser', ''),
            'version': request_data.get('version', '')
        }
        
        device_string = json.dumps(device_data, sort_keys=True)
        return hashlib.sha256(device_string.encode()).hexdigest()

    @staticmethod
    def validate_device(user_id, device_id):
        """Validate if device is known for user"""
        sessions = UserSession.objects.filter(
            user_id=user_id,
            device_id=device_id,
            is_active=True
        )
        return sessions.exists()

    @staticmethod
    def calculate_risk_score(request_data, user):
        """Calculate risk score for login attempt"""
        score = 0
        
        # Check if device is known
        if not SecurityService.validate_device(user.id, request_data['device_id']):
            score += 30
        
        # Check location
        if user.last_login_ip and user.last_login_ip != request_data['ip']:
            score += 20
        
        # Check time of day
        hour = datetime.now().hour
        if hour < 6 or hour > 22:  # Unusual hours
            score += 10
        
        # Check recent failed attempts
        failed_attempts = cache.get(f'failed_login:{user.id}') or 0
        score += failed_attempts * 5
        
        return min(score, 100)  # Cap at 100

