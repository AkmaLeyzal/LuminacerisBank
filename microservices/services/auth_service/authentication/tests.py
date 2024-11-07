from django.test import TestCase

# Create your tests here.
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
        