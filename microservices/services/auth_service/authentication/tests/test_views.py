# authentication/tests/test_views.py
import pytest
from django.urls import reverse
from authentication.models import User, UserSession
from django.core.cache import cache
import jwt

class TestLoginView:
    def test_successful_login(self, api_client, regular_user):
        """Test successful login with valid credentials"""
        url = reverse('login')
        data = {
            'username': 'user',
            'password': 'User@123',
            'device_info': {
                'device_type': 'web',
                'browser': 'chrome',
                'os': 'windows'
            }
        }

        response = api_client.post(url, data, format='json')
        assert response.status_code == 200
        assert 'tokens' in response.data
        assert 'user' in response.data
        assert 'session_id' in response.data

        # Verify token is cached
        token_payload = jwt.decode(
            response.data['tokens']['access_token'],
            options={'verify_signature': False}
        )
        cache_key = f"token:{token_payload['jti']}"
        assert cache.get(cache_key) is not None

    def test_invalid_credentials(self, api_client):
        """Test login with invalid credentials"""
        url = reverse('login')
        data = {
            'username': 'wrong',
            'password': 'wrong',
            'device_info': {
                'device_type': 'web',
                'browser': 'chrome',
                'os': 'windows'
            }
        }

        response = api_client.post(url, data, format='json')
        assert response.status_code == 401
        assert 'error' in response.data

    def test_rate_limiting(self, api_client):
        """Test login rate limiting"""
        url = reverse('login')
        data = {
            'username': 'wrong',
            'password': 'wrong',
            'device_info': {
                'device_type': 'web',
                'browser': 'chrome',
                'os': 'windows'
            }
        }

        # Make 7 requests (limit is 6 per 5 minutes)
        for _ in range(7):
            response = api_client.post(url, data, format='json')

        assert response.status_code == 429
        assert 'error' in response.data

class TestLogoutView:
    def test_successful_logout(self, api_client, access_token):
        """Test successful logout"""
        url = reverse('logout')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = api_client.post(url)
        assert response.status_code == 200

        # Verify token is blacklisted
        token_payload = jwt.decode(
            access_token,
            options={'verify_signature': False}
        )
        blacklist_key = f"blacklist:{token_payload['jti']}"
        assert cache.get(blacklist_key) is not None

    def test_logout_without_token(self, api_client):
        """Test logout without token"""
        url = reverse('logout')
        response = api_client.post(url)
        assert response.status_code == 401
