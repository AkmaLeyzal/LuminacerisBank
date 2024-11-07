
# authentication/tests/test_token_service.py
import pytest
from authentication.services.token_service import TokenService
from django.core.cache import cache
import jwt

class TestTokenService:
    def test_generate_token_pair(self, regular_user):
        """Test generating token pair"""
        tokens = TokenService.generate_token_pair(regular_user)
        
        assert 'access_token' in tokens
        assert 'refresh_token' in tokens
        
        # Verify access token
        access_payload = jwt.decode(
            tokens['access_token'],
            options={'verify_signature': False}
        )
        assert access_payload['user_id'] == regular_user.id
        assert access_payload['token_type'] == 'access'
        
        # Verify refresh token
        refresh_payload = jwt.decode(
            tokens['refresh_token'],
            options={'verify_signature': False}
        )
        assert refresh_payload['user_id'] == regular_user.id
        assert refresh_payload['token_type'] == 'refresh'

    def test_verify_token(self, regular_user):
        """Test token verification"""
        tokens = TokenService.generate_token_pair(regular_user)
        
        # Verify valid token
        payload = TokenService.verify_token(tokens['access_token'])
        assert payload['user_id'] == regular_user.id
        
        # Verify expired token
        expired_payload = {
            'user_id': regular_user.id,
            'exp': datetime.utcnow() - timedelta(hours=1)
        }
        expired_token = jwt.encode(expired_payload, 'secret')
        
        with pytest.raises(jwt.InvalidTokenError):
            TokenService.verify_token(expired_token)

    def test_blacklist_token(self, regular_user):
        """Test token blacklisting"""
        tokens = TokenService.generate_token_pair(regular_user)
        payload = jwt.decode(
            tokens['access_token'],
            options={'verify_signature': False}
        )
        
        TokenService.blacklist_token(
            payload['jti'],
            regular_user.id,
            'Test blacklist'
        )
        
        assert TokenService.is_token_blacklisted(payload['jti'])
