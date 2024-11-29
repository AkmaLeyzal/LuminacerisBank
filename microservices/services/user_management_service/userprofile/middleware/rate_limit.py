# middleware/rate_limit.py
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework import status
import time

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.cache_format = 'rate_limit:{}:{}'
        self.rate_limits = {
            'default': {'calls': 100, 'period': 60},  # 100 calls per minute
            '/api/profiles/': {'calls': 50, 'period': 60},  # 50 calls per minute
            '/api/documents/': {'calls': 30, 'period': 60},  # 30 calls per minute
        }

    def __call__(self, request):
        if not self._should_rate_limit(request.path):
            return self.get_response(request)

        client_ip = self._get_client_ip(request)
        rate_limit_key = self._get_rate_limit_key(request.path)
        
        if not self._check_rate_limit(client_ip, rate_limit_key):
            return Response(
                {'error': 'Rate limit exceeded'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        return self.get_response(request)

    def _should_rate_limit(self, path):
        """Check if path should be rate limited"""
        return any(path.startswith(limit_path) for limit_path in self.rate_limits.keys())

    def _get_client_ip(self, request):
        """Get client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

    def _get_rate_limit_key(self, path):
        """Get appropriate rate limit key for path"""
        for limit_path, limit in self.rate_limits.items():
            if path.startswith(limit_path):
                return limit_path
        return 'default'

    def _check_rate_limit(self, client_ip, rate_limit_key):
        """Check if request is within rate limit"""
        cache_key = self.cache_format.format(client_ip, rate_limit_key)
        limit = self.rate_limits[rate_limit_key]
        
        pipe = cache.pipeline()
        now = time.time()
        
        # Get current window data
        window_data = cache.get(cache_key)
        if not window_data:
            window_data = {'count': 0, 'window_start': now}
        
        # Check if window has expired
        if now - window_data['window_start'] >= limit['period']:
            window_data = {'count': 1, 'window_start': now}
            cache.set(cache_key, window_data, limit['period'])
            return True
        
        # Check if within limit
        if window_data['count'] >= limit['calls']:
            return False
        
        # Increment counter
        window_data['count'] += 1
        cache.set(cache_key, window_data, limit['period'])
        return True