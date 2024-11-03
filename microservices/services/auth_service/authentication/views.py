# auth_service/authentication/views.py
from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from .serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer,
    UserSessionSerializer,
    UserProfileSerializer
)
from .models import User, UserSession
from .utils.redis_utils import RedisService
import jwt
from datetime import datetime
from .kafka_events import AuthKafkaEvents

class RegisterView(views.APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'User registered successfully',
                'user': UserProfileSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(views.APIView):
    def post(self, request):
        # Check rate limit
        kafka_events = AuthKafkaEvents()
        ip = request.META.get('REMOTE_ADDR')
        if not RedisService.check_rate_limit('LOGIN', ip):
            return Response({
                'error': 'Too many login attempts'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        serializer = UserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            RedisService.increment_rate_limit('LOGIN', ip)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        device_info = serializer.validated_data.get('device_info')

        # Generate tokens
        tokens = user.generate_tokens()

        # Create user session
        UserSession.objects.create(
            user=user,
            device_info=device_info or request.META.get('HTTP_USER_AGENT', ''),
            ip_address=ip,
            access_token_jti=tokens['access_token_jti'],
            refresh_token_jti=tokens['refresh_token_jti']
        )

        return Response({
            'tokens': tokens,
            'user': UserProfileSerializer(user).data
        })

        kafka_events.publish_login_event(
            user.id, 
            'success', 
            request.META.get('REMOTE_ADDR'))

class LogoutView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Get token from request
        token = request.auth
        
        # Blacklist the token
        RedisService.blacklist_token(token['jti'])
        
        # Update user session
        UserSession.objects.filter(
            access_token_jti=token['jti']
        ).update(is_active=False)

        return Response({'message': 'Logged out successfully'})

class RefreshTokenView(views.APIView):
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response({
                'error': 'Refresh token is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verify refresh token
            payload = jwt.decode(
                refresh_token,
                settings.JWT_REFRESH_SECRET_KEY,
                algorithms=['HS256']
            )

            # Check if token is blacklisted
            if RedisService.is_token_blacklisted(payload['jti']):
                return Response({
                    'error': 'Token is invalid'
                }, status=status.HTTP_401_UNAUTHORIZED)

            # Get user and generate new tokens
            user = User.objects.get(id=payload['user_id'])
            new_tokens = user.generate_tokens()

            return Response(new_tokens)

        except jwt.ExpiredSignatureError:
            return Response({
                'error': 'Refresh token has expired'
            }, status=status.HTTP_401_UNAUTHORIZED)
        except (jwt.InvalidTokenError, User.DoesNotExist):
            return Response({
                'error': 'Invalid refresh token'
            }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_active_sessions(request):
    sessions = UserSession.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('-last_activity')
    
    serializer = UserSessionSerializer(sessions, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def terminate_session(request, session_id):
    try:
        session = UserSession.objects.get(
            session_id=session_id,
            user=request.user
        )
        
        # Blacklist associated tokens
        RedisService.blacklist_token(session.access_token_jti)
        RedisService.blacklist_token(session.refresh_token_jti)
        
        session.is_active = False
        session.save()
        
        return Response({'message': 'Session terminated successfully'})
    except UserSession.DoesNotExist:
        return Response({
            'error': 'Session not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    serializer = UserProfileSerializer(
        request.user,
        data=request.data,
        partial=True
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)