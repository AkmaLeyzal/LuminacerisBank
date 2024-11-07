# authentication/middleware/error_handling.py
from django.http import JsonResponse
from .logging import CustomLogger
from .exceptions import AuthBaseException
import traceback

class ErrorHandlingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            return self.handle_exception(e)

    def handle_exception(self, exc):
        """Handle different types of exceptions"""
        if isinstance(exc, AuthBaseException):
            return self.handle_auth_exception(exc)
        else:
            return self.handle_unknown_exception(exc)

    def handle_auth_exception(self, exc):
        """Handle known auth service exceptions"""
        CustomLogger.error(
            f'Auth error: {str(exc)}',
            extra={
                'error_code': exc.error_code,
                'status_code': exc.status_code
            }
        )

        return JsonResponse({
            'error': {
                'code': exc.error_code,
                'message': str(exc.detail),
                'status': exc.status_code
            }
        }, status=exc.status_code)

    def handle_unknown_exception(self, exc):
        """Handle unknown exceptions"""
        CustomLogger.error(
            f'Unexpected error: {str(exc)}',
            exc_info=True,
            extra={
                'traceback': traceback.format_exc()
            }
        )

        if settings.DEBUG:
            return JsonResponse({
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': str(exc),
                    'traceback': traceback.format_exc()
                }
            }, status=500)
        else:
            return JsonResponse({
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'An unexpected error occurred'
                }
            }, status=500)
