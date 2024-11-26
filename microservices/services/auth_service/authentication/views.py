# authentication/views.py

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.conf import settings
from .serializers import (
    UserRegistrationSerializer,
    LoginSerializer,
    EmailVerificationSerializer,
    PasswordResetRequestSerializer,
    VerifyOTPSerializer,
    PasswordResetSerializer,
    TokenRefreshSerializer,
    UserResponseSerializer,
    LoginResponseSerializer
)
from .services import (
    RegistrationService,
    AuthenticationService,
    PasswordService
)
from .models import UserSession
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
                tokens = TokenManager.generate_tokens(user.id, user_data)

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
                tokens = TokenManager.generate_tokens(user.id, user_data)

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