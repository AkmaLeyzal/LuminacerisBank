# authentication/middleware.py
from django.http import JsonResponse
from django.conf import settings
from .utils.token_utils import TokenManager
import logging
import re

logger = logging.getLogger(__name__)

class JWTAuthenticationMiddleware:
    EXEMPT_URLS = [
        r'^/api/auth/login/?$',
        r'^/api/auth/register/?$',
        r'^/api/auth/verify-email/?$',
        r'^/api/auth/forgot-password/?$',
        r'^/api/auth/reset-password/?$',
        r'^/admin/?'  # Exclude Django admin URLs if needed
    ]

    def __init__(self, get_response):
        self.get_response = get_response
        # Compile URL patterns for better performance
        self.exempt_urls = [re.compile(url) for url in self.EXEMPT_URLS]

    def __call__(self, request):
        # Skip middleware for exempt URLs
        path = request.path_info.lstrip('/')
        if any(pattern.match(path) for pattern in self.exempt_urls):
            return self.get_response(request)

        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return self.get_response(request)

        try:
            token = self.get_token_from_request(request)
            if not token:
                return JsonResponse(
                    {'error': 'No authentication token provided'}, 
                    status=401
                )

            # Verify and decode token
            decoded_token = TokenManager.verify_token(token)
            if not decoded_token:
                return JsonResponse(
                    {'error': 'Invalid or expired token'}, 
                    status=401
                )

            # Add token data to request
            request.user_id = decoded_token.get('user_id')
            request.token_data = decoded_token
            request.token = token  # Store original token for potential use

        except ValueError as e:
            logger.warning(f"Token validation error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=401)
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}", exc_info=True)
            return JsonResponse(
                {'error': 'Authentication failed'}, 
                status=401
            )

        return self.get_response(request)

    def get_token_from_request(self, request):
        """Extract JWT token from request headers"""
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return None
            
        try:
            # Check for Bearer token format
            auth_parts = auth_header.split()
            if len(auth_parts) != 2 or auth_parts[0].lower() != 'bearer':
                return None
                
            return auth_parts[1]
            
        except (IndexError, AttributeError):
            return None


class CORSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Handle preflight requests
        if request.method == 'OPTIONS':
            response = JsonResponse({}, status=200)
            
        # Add CORS headers
        allowed_origins = settings.CORS_ALLOWED_ORIGINS
        origin = request.headers.get('Origin')
        
        if origin and origin in allowed_origins:
            response['Access-Control-Allow-Origin'] = origin
        elif '*' in allowed_origins:
            response['Access-Control-Allow-Origin'] = '*'
            
        response['Access-Control-Allow-Methods'] = ', '.join([
            'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'
        ])
        response['Access-Control-Allow-Headers'] = ', '.join([
            'Content-Type',
            'Authorization',
            'X-Requested-With',
            'Accept',
            'Origin'
        ])
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Max-Age'] = '86400'  # 24 hours
        
        return response


class RequestLoggingMiddleware:
    """Additional middleware for request logging"""
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('django.request')

    def __call__(self, request):
        # Log request details
        self.logger.info(f"Request: {request.method} {request.path} from {request.META.get('REMOTE_ADDR')}")

        response = self.get_response(request)

        # Log response status
        self.logger.info(f"Response: {response.status_code}")

        return response

    def process_exception(self, request, exception):
        # Log unhandled exceptions
        self.logger.error(f"Unhandled exception: {str(exception)}", exc_info=True)
        return None