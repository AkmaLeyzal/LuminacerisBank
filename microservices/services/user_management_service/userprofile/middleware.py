# middleware.py
import jwt
import requests
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not self._should_bypass_auth(request.path):
            try:
                auth_header = request.META.get('HTTP_AUTHORIZATION')
                if not auth_header or not auth_header.startswith('Bearer '):
                    return self._handle_error('Invalid or missing token')

                token = auth_header.split(' ')[1]
                # Verify token with Auth Service
                user_data = self._verify_token_with_auth_service(token)
                if user_data:
                    request.user_data = user_data
                else:
                    return self._handle_error('Invalid token')

            except Exception as e:
                logger.error(f"Authentication error: {str(e)}")
                return self._handle_error(str(e))

        return self.get_response(request)

    def _verify_token_with_auth_service(self, token):
        """Verify token with Auth Service"""
        try:
            response = requests.post(
                'http://localhost:8000/api/auth/token/verify/',
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                },
                json={'token': token}
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise Exception("Token is invalid or expired")
            else:
                raise Exception(f"Auth service error: {response.text}")

        except requests.RequestException as e:
            logger.error(f"Error communicating with Auth service: {str(e)}")
            raise Exception("Authentication service unavailable")

    def _handle_error(self, message):
        return Response(
            {
                'error': 'Authentication failed',
                'detail': message
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    def _should_bypass_auth(self, path):
        """Check if path should bypass authentication"""
        EXEMPT_PATHS = [
            '/health/',
            '/metrics/',
            '/admin/',
        ]
        return any(path.startswith(exempt) for exempt in EXEMPT_PATHS)