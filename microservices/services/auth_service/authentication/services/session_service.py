# authentication/services/session_service.py
from authentication.models import UserSession
from datetime import datetime, timedelta
from authentication.cache.session_cache import SessionCache
from django.core.cache import cache
from .token_service import TokenService

class SessionService:
    @staticmethod
    def create_session(user, tokens, device_info):
        """Create new user session"""
        session = UserSession.objects.create(
            user=user,
            device_id=device_info['device_id'],
            device_name=device_info.get('device_name'),
            device_type=device_info.get('device_type'),
            user_agent=device_info.get('user_agent'),
            ip_address=device_info.get('ip_address'),
            refresh_token_jti=tokens['refresh_token'],
            expires_at=datetime.utcnow() + timedelta(days=7)
        )

        # Cache session data
        cache_key = f'session:{session.session_id}'
        session_data = {
            'user_id': user.id,
            'device_id': device_info['device_id'],
            'is_active': True,
            'expires_at': session.expires_at.isoformat()
        }
        cache.set(key=cache_key, value=session_data, timeout=604800)  # 7 days

        return session

    @staticmethod
    def end_session(session_id):
        """End user session"""
        session = UserSession.objects.get(session_id=session_id)
        session.is_active = False
        session.save()

        # Remove from cache
        cache.delete(f'session:{session_id}')

        # Blacklist associated tokens
        TokenService.blacklist_token(
            session.refresh_token_jti,
            session.user_id,
            'Session ended'
        )

    @staticmethod
    def get_active_sessions(user_id):
        """Get all active sessions for user"""
        return UserSession.objects.filter(
            user_id=user_id,
            is_active=True
        ).order_by('-last_activity')

    @staticmethod
    def update_session_activity(session_id):
        """Update session last activity"""
        session = UserSession.objects.get(session_id=session_id)
        session.last_activity = datetime.utcnow()
        session.save()

        # Update cache
        cache_key = f'session:{session_id}'
        session_data = cache.get(cache_key)
        if session_data:
            session_data['last_activity'] = session.last_activity.isoformat()
            cache.set(key=cache_key, value=session_data, timeout=604800)