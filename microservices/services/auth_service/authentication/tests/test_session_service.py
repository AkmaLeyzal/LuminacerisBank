# authentication/tests/test_session_service.py
from authentication.services.session_service import SessionService
from authentication.models import UserSession
from django.core.cache import cache

class TestSessionService:
    def test_create_session(self, regular_user):
        """Test session creation"""
        tokens = {
            'refresh_token_jti': 'test_jti'
        }
        device_info = {
            'device_id': 'test_device',
            'device_name': 'Test Device',
            'device_type': 'web',
            'user_agent': 'Chrome',
            'ip': '127.0.0.1'
        }
        
        session = SessionService.create_session(regular_user, tokens, device_info)
        
        assert session.user_id == regular_user.id
        assert session.device_id == device_info['device_id']
        assert session.is_active
        
        # Verify cache
        cache_key = f"session:{session.session_id}"
        cached_data = cache.get(cache_key)
        assert cached_data is not None
        assert cached_data['user_id'] == regular_user.id

    def test_end_session(self, regular_user):
        """Test ending a session"""
        tokens = {
            'refresh_token_jti': 'test_jti'
        }
        device_info = {
            'device_id': 'test_device',
            'device_name': 'Test Device',
            'device_type': 'web',
            'user_agent': 'Chrome',
            'ip': '127.0.0.1'
        }
        
        session = SessionService.create_session(regular_user, tokens, device_info)
        SessionService.end_session(session.session_id)
        
        # Verify session is inactive
        updated_session = UserSession.objects.get(session_id=session.session_id)
        assert not updated_session.is_active
        
        # Verify cache is cleared
        cache_key = f"session:{session.session_id}"
        assert cache.get(cache_key) is None