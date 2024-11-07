# authentication/exceptions.py
from rest_framework.exceptions import APIException
from rest_framework import status
from django.utils.translation import gettext_lazy as _

class AuthBaseException(APIException):
    """Base exception for Auth Service"""
    def __init__(self, detail=None, code=None):
        super().__init__(detail, code)
        self.generate_error_code()

    def generate_error_code(self):
        """Generate unique error code"""
        self.error_code = f"AUTH{self.status_code}"

class InvalidCredentialsException(AuthBaseException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _('Invalid credentials provided.')
    default_code = 'invalid_credentials'

class AccountBlockedException(AuthBaseException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _('Account is blocked.')
    default_code = 'account_blocked'

class TokenValidationException(AuthBaseException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _('Token validation failed.')
    default_code = 'invalid_token'

class RateLimitExceededException(AuthBaseException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = _('Rate limit exceeded.')
    default_code = 'rate_limit_exceeded'

class SessionException(AuthBaseException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Session operation failed.')
    default_code = 'session_error'

class SecurityException(AuthBaseException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _('Security check failed.')
    default_code = 'security_error'
