# authentication/views.py

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import AccessToken
from jwt.exceptions import InvalidTokenError
import jwt
from .serializers import (
    UserRegistrationSerializer,
    LoginSerializer,
    EmailVerificationSerializer,
    PasswordResetRequestSerializer,
    VerifyOTPSerializer,
    PasswordResetSerializer,
    TokenRefreshSerializer,
    UserResponseSerializer,
    LoginResponseSerializer,
    UserVerificationStatusSerializer
)
from .services import (
    RegistrationService,
    AuthenticationService,
    PasswordService
)
from .models import UserSession, User
from .utils.token_utils import TokenManager, TokenBlacklistManager
from .utils.jwt import generate_jwt_payload, get_token_from_request
import logging

logger = logging.getLogger(__name__)

class RegisterView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                # Register user
                user, verification_token = RegistrationService.register_user(
                    serializer.validated_data
                )

                # Generate JWT tokens
                user_data = generate_jwt_payload(user)
                tokens = TokenManager.generate_tokens(str(user.id), user_data)

                # Prepare response
                user_serializer = UserResponseSerializer(user)
                response_data = {
                    'message': 'Registration successful. Please check your email for verification.',
                    'user': user_serializer.data,
                    'tokens': tokens
                }

                response = Response(response_data, status=status.HTTP_201_CREATED)

                # Set JWT cookie if enabled
                if settings.JWT_AUTH.get('JWT_AUTH_COOKIE'):
                    response.set_cookie(
                        settings.JWT_AUTH['JWT_AUTH_COOKIE'],
                        tokens['access_token'],
                        httponly=True,
                        secure=settings.JWT_AUTH.get('JWT_AUTH_COOKIE_SECURE', False),
                        samesite=settings.JWT_AUTH.get('JWT_AUTH_COOKIE_SAMESITE', 'Lax'),
                        domain=settings.JWT_AUTH.get('JWT_AUTH_COOKIE_DOMAIN')
                    )

                return response

            except ValueError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                logger.error(f"Registration error: {str(e)}")
                return Response(
                    {'error': 'Registration failed. Please try again.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# authentication/views.py (continuation)

class LoginView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                # Prepare request data
                request_data = {
                    'ip_address': request.META.get('REMOTE_ADDR'),
                    'user_agent': request.META.get('HTTP_USER_AGENT'),
                    **serializer.validated_data
                }

                # Authenticate user
                user = AuthenticationService.authenticate_user(
                    email=serializer.validated_data['email'],
                    password=serializer.validated_data['password'],
                    request_data=request_data
                )

                # Generate JWT tokens
                user_data = generate_jwt_payload(user)
                tokens = TokenManager.generate_tokens(str(user.id), user_data)

                # Create user session
                AuthenticationService.create_session(user, tokens, request_data)

                # Prepare response
                response_serializer = LoginResponseSerializer({
                    'user': user,
                    'tokens': tokens,
                    'message': 'Login successful'
                })
                
                response = Response(
                    response_serializer.data,
                    status=status.HTTP_200_OK
                )

                # Set JWT cookie if enabled
                if settings.JWT_AUTH.get('JWT_AUTH_COOKIE'):
                    response.set_cookie(
                        settings.JWT_AUTH['JWT_AUTH_COOKIE'],
                        tokens['access_token'],
                        httponly=True,
                        secure=settings.JWT_AUTH.get('JWT_AUTH_COOKIE_SECURE', False),
                        samesite=settings.JWT_AUTH.get('JWT_AUTH_COOKIE_SAMESITE', 'Lax'),
                        domain=settings.JWT_AUTH.get('JWT_AUTH_COOKIE_DOMAIN')
                    )

                return response

            except ValueError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                logger.error(f"Login error: {str(e)}")
                return Response(
                    {'error': 'Login failed. Please try again.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            token = get_token_from_request(request)
            decoded_token = TokenManager.verify_token(token)

            # Blacklist current token
            TokenBlacklistManager.blacklist_token(
                token_jti=decoded_token['jti'],
                user_id=request.user.id,
                reason="User logout",
                blacklisted_by="user"
            )
            
            # Invalidate user session
            UserSession.objects.filter(
                user_id=request.user.id,
                access_token_jti=decoded_token['jti']
            ).update(is_active=False)

            response = Response({
                'message': 'Logged out successfully'
            })

            # Clear JWT cookie if enabled
            if settings.JWT_AUTH.get('JWT_AUTH_COOKIE'):
                response.delete_cookie(
                    settings.JWT_AUTH['JWT_AUTH_COOKIE'],
                    domain=settings.JWT_AUTH.get('JWT_AUTH_COOKIE_DOMAIN'),
                    samesite=settings.JWT_AUTH.get('JWT_AUTH_COOKIE_SAMESITE', 'Lax')
                )

            return response

        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response(
                {'error': 'Logout failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class EmailVerificationView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = EmailVerificationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                RegistrationService.verify_email(serializer.validated_data['token'])
                return Response({
                    'message': 'Email verified successfully.'
                }, status=status.HTTP_200_OK)

            except ValueError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                logger.error(f"Email verification error: {str(e)}")
                return Response(
                    {'error': 'Verification failed. Please try again.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetRequestView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                PasswordService.initiate_reset(serializer.validated_data['email'])
                return Response({
                    'message': 'If an account exists with this email, you will receive a password reset OTP.'
                }, status=status.HTTP_200_OK)

            except Exception as e:
                logger.error(f"Password reset request error: {str(e)}")
                return Response(
                    {'error': 'Failed to process password reset request.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = VerifyOTPSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                is_valid = PasswordService.verify_otp(
                    serializer.validated_data['email'],
                    serializer.validated_data['otp']
                )

                if not is_valid:
                    return Response(
                        {'error': 'Invalid or expired OTP'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                return Response({
                    'message': 'OTP verified successfully'
                }, status=status.HTTP_200_OK)

            except Exception as e:
                logger.error(f"OTP verification error: {str(e)}")
                return Response(
                    {'error': 'Failed to verify OTP'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = PasswordResetSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                success = PasswordService.reset_password(
                    serializer.validated_data['token'],
                    serializer.validated_data['new_password']
                )

                if not success:
                    return Response(
                        {'error': 'Password reset failed'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                return Response({
                    'message': 'Password reset successful'
                }, status=status.HTTP_200_OK)

            except ValueError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                logger.error(f"Password reset error: {str(e)}")
                return Response(
                    {'error': 'Failed to reset password'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TokenRefreshView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = TokenRefreshSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                new_tokens = TokenManager.refresh_access_token(
                    serializer.validated_data['refresh_token']
                )
                return Response(new_tokens, status=status.HTTP_200_OK)

            except ValueError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            except Exception as e:
                logger.error(f"Token refresh error: {str(e)}")
                return Response(
                    {'error': 'Token refresh failed'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserVerificationStatusView(APIView):
    """View for checking user verification status"""
    
    def get_permissions(self):
        """
        Allow access to microservices using service authentication
        or regular authenticated users for self-check
        """
        if 'Service-Auth-Key' in self.request.headers:
            return []
        return [IsAuthenticated()]

    def get(self, request, user_id=None):
        try:
            # Check if request is from a microservice
            service_auth_key = request.headers.get('Service-Auth-Key')
            is_service_request = service_auth_key == settings.SERVICE_AUTH_KEY

            # If it's a service request, allow checking any user
            # If it's a user request, only allow checking self
            if is_service_request:
                user = get_object_or_404(User, id=user_id)
            else:
                # Regular users can only check their own status
                if str(request.user.user_id) != str(user_id):
                    return Response(
                        {'error': 'Not authorized to view this user\'s status'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                user = request.user

            serializer = UserVerificationStatusSerializer(user)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error checking user verification status: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve verification status'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ServiceUserVerificationView(APIView):
    """Internal API for microservices to verify users"""

    def get(self, request, user_id):
        try:
            # Verify service authentication
            service_auth_key = request.headers.get('Service-Auth-Key')
            if not service_auth_key or service_auth_key != settings.SERVICE_AUTH_KEY:
                return Response(
                    {'error': 'Invalid service authentication'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Get user and verification status
            user = get_object_or_404(User, id=user_id)
            serializer = UserVerificationStatusSerializer(user)

            # Add additional service-specific information
            response_data = serializer.data
            response_data.update({
                'service_verification': {
                    'is_eligible_for_services': user.status == User.Status.ACTIVE,
                    'verified_at': user.updated_at.isoformat() if user.is_email_verified else None,
                    'user_type': 'PERSONAL',  # You might want to make this dynamic
                    'kyc_status': 'VERIFIED' if user.is_email_verified else 'PENDING'
                }
            })

            return Response(response_data)

        except Exception as e:
            logger.error(f"Error in service verification: {str(e)}")
            return Response(
                {'error': 'Internal service error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )    
        
class TokenVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token') or request.headers.get('Authorization', '').split(' ')[1]
        
        if not token:
            return Response(
                {'error': 'Token is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Decode and verify token
            decoded_token = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=['HS256']
            )

            # Get user from token
            user_id = decoded_token.get('user_id')
            if not user_id:
                raise InvalidTokenError('Invalid token payload')

            return Response({
                'status': 'success',
                'user_id': user_id,
                'token_type': decoded_token.get('token_type'),
                'exp': decoded_token.get('exp')
            })

        except InvalidTokenError as e:
            return Response(
                {
                    'error': 'Token verification failed',
                    'detail': str(e)
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {
                    'error': 'Token verification failed',
                    'detail': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )