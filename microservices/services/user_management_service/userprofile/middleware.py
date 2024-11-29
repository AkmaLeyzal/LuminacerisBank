# middleware.py
import jwt
import requests
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from django.core.cache import cache

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not self._should_bypass_auth(request.path):
            auth_header = request.META.get('HTTP_AUTHORIZATION')
            if not auth_header or not auth_header.startswith('Bearer '):
                return Response(
                    {'error': 'Invalid or missing token'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )

            token = auth_header.split(' ')[1]
            try:
                # Verify with Auth Service
                self._verify_token(token)
                # Add user info to request
                request.user_data = self._get_user_data(token)
            except Exception as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )

        return self.get_response(request)

    def _verify_token(self, token):
        """Verify token with Auth Service"""
        cache_key = f'token_verification:{token}'
        verification_result = cache.get(cache_key)

        if not verification_result:
            response = requests.post(
                'http://localhost:8001/api/auth/verify/',
                headers={'Authorization': f'Bearer {token}'}
            )
            if response.status_code != 200:
                raise Exception('Invalid token')
            
            # Cache the verification result for 5 minutes
            cache.set(cache_key, True, 300)

    def _get_user_data(self, token):
        """Decode token to get user data"""
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except jwt.DecodeError:
            raise Exception('Invalid token format')

    def _should_bypass_auth(self, path):
        """Check if path should bypass authentication"""
        EXEMPT_PATHS = [
            '/health/',
            '/metrics/',
        ]
        return any(path.startswith(exempt) for exempt in EXEMPT_PATHS)