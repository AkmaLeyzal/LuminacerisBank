# authentication/middleware/security_middleware.py
from django.http import JsonResponse
from django.core.cache import cache
from datetime import datetime
import jwt
import logging

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            # Skip middleware for public endpoints
            if self._is_public_endpoint(request.path):
                return self.get_response(request)

            # Check rate limiting
            if not self._check_rate_limit(request):
                return JsonResponse(
                    {'error': 'Rate limit exceeded'},
                    status=429
                )

            # Validate JWT and security requirements
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return JsonResponse(
                    {'error': 'Invalid authorization header'},
                    status=401
                )

            token = auth_header.split(' ')[1]
            try:
                payload = self._validate_token(token)
                request.user_id = payload.get('user_id')
                
                # Check if user requires additional verification
                if self._requires_verification(payload['user_id']):
                    return JsonResponse(
                        {'error': 'Additional verification required'},
                        status=403
                    )

                # Update last activity
                self._update_last_activity(payload['user_id'])

            except jwt.InvalidTokenError as e:
                return JsonResponse(
                    {'error': str(e)},
                    status=401
                )

            return self.get_response(request)

        except Exception as e:
            logger.error(f"Security middleware error: {str(e)}", exc_info=True)
            return JsonResponse(
                {'error': 'Internal server error'},
                status=500
            )

    def _is_public_endpoint(self, path):
        """Check if endpoint is public"""
        public_paths = [
            '/api/auth/login',
            '/api/auth/register',
            '/api/auth/password/reset',
            '/api/health'
        ]
        return any(path.startswith(p) for p in public_paths)

    def _check_rate_limit(self, request):
        """Check API rate limiting"""
        ip = request.META.get('REMOTE_ADDR')
        path = request.path

        # Rate limit key combining IP and endpoint
        rate_key = f"rate:api:{ip}:{path}"
        
        # Get current count
        count = cache.get(rate_key) or 0
        
        if count >= 100:  # 100 requests per minute limit
            return False
        
        # Increment counter
        cache.set(rate_key, count + 1, timeout=60)
        return True

    def _validate_token(self, token):
        """Validate JWT token"""
        try:
            # First decode without verification to get JTI
            unverified = jwt.decode(token, options={'verify_signature': False})
            token_id = unverified.get('jti')

            # Check blacklist
            blacklist_key = f"blacklist:{token_id}"
            if cache.get(blacklist_key):
                raise jwt.InvalidTokenError('Token is blacklisted')

            # Verify token fully
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=['HS256']
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise jwt.InvalidTokenError('Token has expired')
        except jwt.InvalidTokenError as e:
            raise jwt.InvalidTokenError(str(e))

    def _requires_verification(self, user_id):
        """Check if user requires additional verification"""
        verify_key = f"user:{user_id}:requires_verification"
        return cache.get(verify_key, False)

    def _update_last_activity(self, user_id):
        """Update user's last activity timestamp"""
        activity_key = f"user:{user_id}:last_activity"
        cache.set(activity_key, datetime.utcnow().isoformat(), timeout=3600)
