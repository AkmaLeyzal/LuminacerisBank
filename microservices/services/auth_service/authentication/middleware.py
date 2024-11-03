# microservices/services/auth_service/authentication/middleware.py
from django.http import JsonResponse
from django.core.cache import cache
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
import jwt
import logging

logger = logging.getLogger(__name__)

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._should_skip_auth(request.path):
            return self.get_response(request)

        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse(
                {'error': 'Invalid authorization header'},
                status=401
            )

        token = auth_header.split(' ')[1]
        try:
            # Validate token
            decoded_token = self._validate_token(token)
            
            # Check if token is blacklisted
            if self._is_token_blacklisted(decoded_token['jti']):
                return JsonResponse(
                    {'error': 'Token is blacklisted'},
                    status=401
                )

            # Add user info to request
            request.user_id = decoded_token['user_id']
            request.user_roles = decoded_token.get('roles', [])
            
            return self.get_response(request)

        except (InvalidToken, TokenError) as e:
            logger.warning(f"Token validation failed: {str(e)}")
            return JsonResponse(
                {'error': 'Invalid token'},
                status=401
            )
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return JsonResponse(
                {'error': 'Authentication failed'},
                status=500
            )

    def _should_skip_auth(self, path: str) -> bool:
        """Check if path should skip authentication"""
        public_paths = [
            '/api/auth/login/',
            '/api/auth/register/',
            '/health/',
        ]
        return any(path.startswith(p) for p in public_paths)

    def _validate_token(self, token: str) -> dict:
        """Validate JWT token"""
        try:
            # First decode without verification to get JTI
            unverified = jwt.decode(token, options={'verify_signature': False})
            token_jti = unverified['jti']

            # Check cache for valid token
            cached_token = cache.get(f'token:{token_jti}')
            if cached_token:
                return cached_token

            # Verify token if not in cache
            decoded = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=['HS256']
            )

            # Cache validated token
            cache.set(
                f'token:{token_jti}',
                decoded,
                timeout=300  # 5 minutes
            )

            return decoded

        except jwt.ExpiredSignatureError:
            raise InvalidToken('Token has expired')
        except jwt.InvalidTokenError:
            raise InvalidToken('Invalid token')

    def _is_token_blacklisted(self, token_jti: str) -> bool:
        """Check if token is blacklisted"""
        return cache.get(f'blacklist:{token_jti}', False)