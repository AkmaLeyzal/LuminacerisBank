# microservices/services/auth_service/authentication/services.py
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from typing import Dict, Tuple
from .models import User, UserSession, TokenBlacklist, SecurityAuditLog
from kafka_cloud.producer import KafkaProducer
from kafka_cloud.topics import KafkaTopics
import jwt
import uuid
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.kafka_producer = KafkaProducer()
        self.cache_ttl = settings.CACHE_TTL

    async def authenticate_user(self, username: str, password: str, request_data: Dict) -> Tuple[User, Dict]:
        """Authenticate user and return tokens"""
        try:
            # Get user from cache first
            cache_key = f'user:{username}'
            user = cache.get(cache_key)

            if not user:
                user = await User.objects.select_related().get(username=username)
                cache.set(cache_key, user, timeout=self.cache_ttl['USER_SESSION'])

            # Check user status
            if user.is_blocked:
                await self._log_security_event(
                    user, 
                    'LOGIN_BLOCKED',
                    request_data
                )
                raise ValidationError("Account is blocked")

            # Check password
            if not check_password(password, user.password_hash):
                await self._handle_failed_login(user, request_data)
                raise ValidationError("Invalid credentials")

            # Generate tokens
            tokens = self._generate_tokens(user)

            # Create session
            await self._create_session(user, tokens, request_data)

            # Update user login info
            user.last_login_date = datetime.now()
            user.last_login_ip = request_data.get('ip_address')
            await user.save()
            cache.delete(cache_key)  # Invalidate user cache

            # Publish login event
            self.kafka_producer.produce(
                KafkaTopics.USER_EVENTS,
                {
                    'event_type': 'USER_LOGIN',
                    'data': {
                        'user_id': user.id,
                        'username': user.username,
                        'status': 'success',
                        'ip_address': request_data.get('ip_address'),
                        'timestamp': str(datetime.now())
                    }
                }
            )

            return user, tokens

        except User.DoesNotExist:
            logger.warning(f"Login attempt with non-existent username: {username}")
            raise ValidationError("Invalid credentials")
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise

    def _generate_tokens(self, user: User) -> Dict:
        """Generate access and refresh tokens"""
        access_token_jti = str(uuid.uuid4())
        refresh_token_jti = str(uuid.uuid4())

        # Access token payload
        access_payload = {
            'token_type': 'access',
            'jti': access_token_jti,
            'user_id': user.id,
            'username': user.username,
            'exp': datetime.utcnow() + timedelta(minutes=settings.JWT_SETTINGS['ACCESS_TOKEN_LIFETIME'])
        }

        # Refresh token payload
        refresh_payload = {
            'token_type': 'refresh',
            'jti': refresh_token_jti,
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(days=settings.JWT_SETTINGS['REFRESH_TOKEN_LIFETIME'])
        }

        return {
            'access_token': jwt.encode(
                access_payload,
                settings.SECRET_KEY,
                algorithm=settings.JWT_SETTINGS['ALGORITHM']
            ),
            'refresh_token': jwt.encode(
                refresh_payload,
                settings.SECRET_KEY,
                algorithm=settings.JWT_SETTINGS['ALGORITHM']
            ),
            'access_token_jti': access_token_jti,
            'refresh_token_jti': refresh_token_jti,
            'token_type': 'Bearer',
            'expires_in': settings.JWT_SETTINGS['ACCESS_TOKEN_LIFETIME'] * 60
        }

    async def _handle_failed_login(self, user: User, request_data: Dict):
        """Handle failed login attempt"""
        cache_key = f'login_attempts:{user.id}'
        attempts = cache.get(cache_key, 0) + 1
        cache.set(cache_key, attempts, timeout=settings.LOGIN_ATTEMPT_TIMEOUT * 60)

        user.failed_login_attempts = attempts
        user.last_failed_login = datetime.now()

        if attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.is_blocked = True
            user.blocked_at = datetime.now()
            user.block_reason = 'Too many failed login attempts'

            self.kafka_producer.produce(
                KafkaTopics.SECURITY_EVENTS,
                {
                    'event_type': 'ACCOUNT_BLOCKED',
                    'data': {
                        'user_id': user.id,
                        'username': user.username,
                        'reason': 'Too many failed login attempts',
                        'ip_address': request_data.get('ip_address'),
                        'timestamp': str(datetime.now())
                    }
                }
            )

        await user.save()