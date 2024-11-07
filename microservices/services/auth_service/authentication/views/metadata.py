# authentication/views/metadata.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.conf import settings
import platform
import sys

class MetadataView(APIView):
    """Endpoint untuk mendapatkan informasi tentang API"""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            'name': 'Auth Service API',
            'version': '1.0.0',
            'endpoints': {
                'login': '/api/auth/login/',
                'logout': '/api/auth/logout/',
                'token_refresh': '/api/auth/token/refresh/',
                'health': '/api/auth/health/',
                'metadata': '/api/auth/metadata/'
            },
            'environment': settings.ENV_NAME,
            'debug_mode': settings.DEBUG,
            'python_version': platform.python_version(),
            'django_version': sys.modules['django'].__version__
        })

class HealthCheckView(APIView):
    """Health check endpoint"""
    permission_classes = [AllowAny]

    def get(self, request):
        from django.db import connection
        from django.core.cache import cache
        
        # Check database
        db_status = True
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
        except Exception:
            db_status = False

        # Check Redis
        cache_status = True
        try:
            cache.set('health_check', 'ok', 1)
            cache_value = cache.get('health_check')
            cache_status = cache_value == 'ok'
        except Exception:
            cache_status = False

        # Overall status
        status = 'healthy' if db_status and cache_status else 'unhealthy'

        return Response({
            'status': status,
            'timestamp': datetime.utcnow().isoformat(),
            'components': {
                'database': 'up' if db_status else 'down',
                'cache': 'up' if cache_status else 'down'
            }
        })
