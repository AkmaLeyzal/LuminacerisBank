# authentication/views.py
from rest_framework import serializers
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.cache import cache
from .services import TokenService, SecurityService, SessionService
from kafka_cloud.producer import KafkaProducer
from kafka_cloud.topics import KafkaTopics
import logging
from .models import *
from datetime import datetime
from authentication.utils.logging import CustomLogger
from authentication.utils.decorators import log_execution_time, handle_exceptions
from authentication.cache.token_cache import TokenCache
from authentication.cache.session_cache import SessionCache
from authentication.cache.rate_limit import RateLimiter
import jwt
from .serializers import (
    UserSerializer,
    UserSession,
    LoginRequestSerializer,
    RegisterSerializer
    )
from .exceptions import (
    InvalidCredentialsException,
    AccountBlockedException,
    TokenValidationException,
    RateLimitExceededException,
    SecurityException
)
from authentication.services.token_service import TokenService

logger = logging.getLogger(__name__)
kafka_producer = KafkaProducer()

class LoginView(APIView):
    permission_classes = [AllowAny]

    def __init__(self):
        self.token_cache = TokenCache()
        self.session_cache = SessionCache()
        self.rate_limiter = RateLimiter()

    @log_execution_time
    @handle_exceptions({
        ValueError: InvalidCredentialsException,
        jwt.InvalidTokenError: TokenValidationException,
        'RateLimitExceeded': RateLimitExceededException
    })
    def post(self, request):
        try:
            if not self.rate_limiter.check_rate_limit(
                f"login:{request.META.get('REMOTE_ADDR')}",
                limit=6,
                window=300
            ):
                raise RateLimitExceededException()
            
            CustomLogger.info(
                'Login attempt',
                extra={'username': request.data.get('username')}
            )
            serializer = LoginRequestSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Rate limit check
            if not SecurityService.check_rate_limit(
                f"login:{request.META.get('REMOTE_ADDR')}", 
                limit=6, 
                window=300
            ):
                return Response(
                    {'error': 'Too many login attempts'}, 
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            # Authenticate user
            user = authenticate(
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password']
            )

            if not user:
                # Increment failed attempts counter
                cache_key = f"failed_login:{serializer.validated_data['username']}"
                cache.incr(cache_key, default=0)
                cache.expire(cache_key, 300)  # 5 minutes

                # Publish failed login event
                kafka_producer.produce(
                    topic=KafkaTopics.SECURITY_EVENTS,
                    key=str(user.id) if user else None,
                    value={
                        'event_type': 'LOGIN_FAILED',
                        'username': serializer.validated_data['username'],
                        'ip_address': request.META.get('REMOTE_ADDR'),
                        'user_agent': request.META.get('HTTP_USER_AGENT'),
                        'timestamp': datetime.utcnow().isoformat(),
                        'reason': 'Invalid credentials'
                    }
                )

                return Response(
                    {'error': 'Invalid credentials'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Generate device ID
            device_info = serializer.validated_data['device_info']
            device_info.update({
                'ip': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT')
            })
            device_id = SecurityService.generate_device_id(device_info)
            device_info['device_id'] = device_id

            # Calculate risk score
            risk_score = SecurityService.calculate_risk_score(device_info, user)

            # Generate tokens
            tokens = TokenService.generate_token_pair(user)

            # Cache tokens
            access_payload = jwt.decode(tokens['access_token'], options={'verify_signature': False})
            refresh_payload = jwt.decode(tokens['refresh_token'], options={'verify_signature': False})
            
            self.token_cache.cache_token(access_payload['jti'], access_payload, 'access')
            self.token_cache.cache_token(refresh_payload['jti'], refresh_payload, 'refresh')
            
            # Cache session
            session = SessionService.create_session(user, tokens, device_info)
            self.session_cache.cache_session(
                str(session.session_id),
                {
                    'user_id': user.id,
                    'device_id': device_info['device_id'],
                    'is_active': True,
                    'created_at': datetime.utcnow().isoformat()
                }
            )
            # Update user login info
            user.last_login_ip = request.META.get('REMOTE_ADDR')
            user.last_login_date = datetime.utcnow()
            user.save()

            # Publish successful login event
            kafka_producer.produce(
                topic=KafkaTopics.SECURITY_EVENTS,
                key=str(user.id),
                value={
                    'event_type': 'LOGIN_SUCCESS',
                    'user_id': user.id,
                    'session_id': str(session.session_id),
                    'ip_address': request.META.get('REMOTE_ADDR'),
                    'user_agent': request.META.get('HTTP_USER_AGENT'),
                    'device_id': device_id,
                    'risk_score': risk_score,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )

            CustomLogger.info(
                'Login successful',
                extra={'user_id': user.id}
            )
            
            return Response({
                'tokens': tokens,
                'user': UserSerializer(user).data,
                'session_id': str(session.session_id)
            })
        
        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            CustomLogger.error(
                'Login failed',
                exc_info=True,
                extra={
                    'username': request.data.get('username'),
                    'error': str(e)
                }
            )
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    def get(self, request):
        """Handle GET request with helpful message"""
        return Response({
            'message': 'This endpoint only accepts POST requests',
            'method': 'POST',
            'required_fields': {
                'username': 'string',
                'password': 'string',
                'device_info': {
                    'device_type': 'string (optional)',
                    'browser': 'string (optional)',
                    'os': 'string (optional)'
                }
            },
            'example_request': {
                'username': 'user@example.com',
                'password': '********',
                'device_info': {
                    'device_type': 'web',
                    'browser': 'chrome',
                    'os': 'windows'
                }
            }
        }, status=405)
class LogoutView(APIView):
    def post(self, request):
        try:
            # Get token from authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return Response(
                    {'error': 'Invalid authorization header'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            token = auth_header.split(' ')[1]
            
            # Verify token
            try:
                payload = TokenService.verify_token(token)
            except jwt.InvalidTokenError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # End session
            session_id = request.data.get('session_id')
            if session_id:
                SessionService.end_session(session_id)

            # Blacklist tokens
            TokenService.blacklist_token(
                payload['jti'],
                payload['user_id'],
                'User logout'
            )

            # Publish logout event
            kafka_producer.produce(
                topic=KafkaTopics.SECURITY_EVENTS,
                key=str(payload['user_id']),
                value={
                    'event_type': 'LOGOUT',
                    'user_id': payload['user_id'],
                    'session_id': session_id,
                    'ip_address': request.META.get('REMOTE_ADDR'),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )

            return Response(status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Logout error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Verify refresh token
            payload = TokenService.verify_token(refresh_token, token_type='refresh')

            # Rate limit check
            if not SecurityService.check_rate_limit(
                f"refresh:{payload['user_id']}", 
                limit=10, 
                window=60
            ):
                return Response(
                    {'error': 'Too many refresh attempts'},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            # Get user
            user = User.objects.get(id=payload['user_id'])

            # Generate new token pair
            new_tokens = TokenService.generate_token_pair(user)

            # Blacklist old refresh token
            TokenService.blacklist_token(
                payload['jti'],
                payload['user_id'],
                'Token refresh'
            )

            # Publish token refresh event
            kafka_producer.produce(
                topic=KafkaTopics.SECURITY_EVENTS,
                key=str(user.id),
                value={
                    'event_type': 'TOKEN_REFRESH',
                    'user_id': user.id,
                    'ip_address': request.META.get('REMOTE_ADDR'),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )

            return Response(new_tokens)

        except jwt.InvalidTokenError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    def get(self, request):
        """Handle GET request with helpful message"""
        return Response({
            'message': 'This endpoint only accepts POST requests',
            'method': 'POST',
            'required_fields': {
                'refresh_token': 'string'
            },
            'headers': {
                'Authorization': 'Bearer your_access_token (optional)'
            },
            'example_request': {
                'refresh_token': 'your_refresh_token_here'
            }
        }, status=405)
    
class RegisterView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            try:
                cache.set('test_key', 'test_value', timeout=10)
                test_value = cache.get('test_key')
                logger.info(f"Redis connection test: {test_value}")
            except Exception as redis_error:
                logger.error(f"Redis connection error: {str(redis_error)}")
                # Continue even if Redis fails
                pass

            serializer = RegisterSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Create user
            user = serializer.save()

            # Assign default role
            default_role = Role.objects.get_or_create(
                name='USER',
                defaults={
                    'description': 'Default role for registered users',
                    'permissions': {
                        'permissions': ['view_profile', 'edit_profile', 'make_transaction']
                    }
                }
            )[0]
            user.roles.add(default_role)
            
            # Generate tokens
            tokens = TokenService.generate_token_pair(user)
            
            # Create initial session
            device_info = {
                'device_id': request.META.get('DEVICE_ID', 'unknown_device_id'),  
                'device_name': request.META.get('DEVICE_NAME', 'Unknown Device'),  
                'device_type': request.META.get('DEVICE_TYPE', 'Unknown Type'),
                'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown Agent'),
                'ip_address': request.META.get('REMOTE_ADDR', '0.0.0.0')
            }
            session = SessionService.create_session(user, tokens=tokens, device_info=device_info)
            
            return Response({
                'message': 'Registration successful',
                'tokens': tokens,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
            
        except serializers.ValidationError as e:
            return Response({
                'error': 'Validation Error',
                'details': e.detail
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Registration error: {str(e)}", exc_info=True)
            return Response({
                'error': 'Registration failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)