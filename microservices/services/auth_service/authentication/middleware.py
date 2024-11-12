# authentication/middleware.py

from .utils.token_utils import TokenManager
from django.http import JsonResponse
from django.conf import settings

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'api/auth/login' in request.path or \
           'api/auth/register' in request.path or \
           'api/auth/verify-email' in request.path:
            return self.get_response(request)

        try:
            token = get_token_from_request(request)
            if not token:
                return JsonResponse(
                    {'error': 'No authentication token provided'}, 
                    status=401
                )

            decoded_token = TokenManager.verify_token(token)
            if not decoded_token:
                return JsonResponse(
                    {'error': 'Invalid authentication token'}, 
                    status=401
                )

            # Add user data to request
            request.user_id = decoded_token['user_id']
            request.user_data = decoded_token.get('user_data', {})
            
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return JsonResponse(
                {'error': 'Authentication failed'}, 
                status=401
            )

        return self.get_response(request)

class CORSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Add CORS headers for microfrontend integration
        response['Access-Control-Allow-Origin'] = settings.CORS_ALLOWED_ORIGINS
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response['Access-Control-Allow-Credentials'] = 'true'
        
        return response
