# auth_service/authentication/middleware.py
from django.http import JsonResponse
from django.core.cache import cache
from datetime import datetime
import jwt
from .models import User, TokenBlacklist

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._should_skip_auth(request.path):
            return self.get_response(request)

        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Invalid authorization header'}, status=401)

        token = auth_header.split(' ')[1]
        try:
            # Get token ID without verification first
            unverified_payload = jwt.decode(
                token,
                options={'verify_signature': False}
            )
            token_id = unverified_payload.get('jti')

            # Check Redis cache first
            cached_status = self._get_cached_token_status(token_id)
            if cached_status == 'blacklisted':
                return JsonResponse({'error': 'Token is blacklisted'}, status=401)

            # Verify token fully
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=['HS256']
            )

            # Check if user is blocked
            user_blocked = cache.get(f'user:blocked:{payload["user_id"]}')
            if user_blocked:
                return JsonResponse({'error': 'User is blocked'}, status=401)

            # Attach user and payload to request
            request.user_payload = payload
            return self.get_response(request)

        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'Token has expired'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'error': 'Invalid token'}, status=401)

    def _should_skip_auth(self, path):
        """Check if path should skip authentication"""
        public_paths = [
            '/api/auth/login/',
            '/api/auth/register/',
            '/api/auth/password/reset/',
            '/api/health/',
        ]
        return any(path.startswith(p) for p in public_paths)

    def _get_cached_token_status(self, token_id):
        """Get token status from Redis cache"""
        return cache.get(f'token:{token_id}')