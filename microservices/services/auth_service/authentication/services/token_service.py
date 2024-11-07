# authentication/services/token_service.py
from django.conf import settings
from django.core.cache import cache
from datetime import datetime, timedelta
from authentication.models import TokenBlacklist
import jwt
import uuid
import redis
import logging
import json

logger = logging.getLogger(__name__)

class TokenService:
    @staticmethod
    def get_redis_client():
        """Get Redis client with proper configuration"""
        try:
            return redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                db=0
            )
        except Exception as e:
            logger.error(f"Redis connection error: {str(e)}")
            return None

    @staticmethod
    def generate_token_pair(user):
        """Generate access and refresh token pair"""
        access_token_id = str(uuid.uuid4())
        refresh_token_id = str(uuid.uuid4())
        
        # Access token payload
        access_payload = {
            'token_type': 'access',
            'user_id': user.id,
            'email': user.email,
            'roles': [role.name for role in user.roles.all()] if hasattr(user, 'roles') else [],
            'permissions': user.get_all_permissions() if hasattr(user, 'get_all_permissions') else [],
            'jti': access_token_id,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(minutes=30)
        }
        
        # Refresh token payload
        refresh_payload = {
            'token_type': 'refresh',
            'user_id': user.id,
            'jti': refresh_token_id,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(days=7)
        }

        # Generate tokens
        access_token = jwt.encode(
            access_payload,
            settings.JWT_SECRET_KEY,
            algorithm='HS256'
        )
        
        refresh_token = jwt.encode(
            refresh_payload,
            settings.JWT_REFRESH_SECRET_KEY,
            algorithm='HS256'
        )

        # Try to cache token data
        try:
            TokenService._cache_token_data(access_token_id, access_payload)
            TokenService._cache_token_data(refresh_token_id, refresh_payload)
        except Exception as cache_error:
            logger.warning(f"Failed to cache token data: {str(cache_error)}")
            # Continue without caching


        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 1800,  # 30 minutes
            'token_type': 'Bearer'
        }

    @staticmethod
    def _cache_token_data(token_id, payload):
        """Cache token data in Redis"""
        try:
            cache_key = f'token:{token_id}'
            token_data = {
                'user_id': payload['user_id'],
                'token_type': payload['token_type'],
                'exp': payload['exp'].timestamp() if isinstance(payload['exp'], datetime) else payload['exp'],
                'is_blacklisted': False
            }
            
            # Use basic SET operation instead of Django's cache
            redis_client = TokenService.get_redis_client()
            if redis_client:
                redis_client.setex(
                    cache_key,
                    int((payload['exp'] - datetime.utcnow()).total_seconds()),
                    json.dumps(token_data)
                )
        except Exception as e:
            logger.warning(f"Token caching failed: {str(e)}")
            # Continue without caching

    @staticmethod
    def verify_token(token, token_type='access'):
        """Verify and decode JWT token"""
        try:
            # First decode without verification to get JTI
            unverified_payload = jwt.decode(token, options={'verify_signature': False})
            token_id = unverified_payload.get('jti')

            # Check blacklist
            if TokenService.is_token_blacklisted(token_id):
                raise jwt.InvalidTokenError('Token is blacklisted')

            # Verify token signature and claims
            secret_key = settings.JWT_SECRET_KEY if token_type == 'access' else settings.JWT_REFRESH_SECRET_KEY
            payload = jwt.decode(
                token,
                secret_key,
                algorithms=['HS256'],
                options={
                    'verify_exp': True,
                    'require': ['exp', 'iat', 'jti', 'user_id', 'token_type']
                }
            )

            # Additional validations
            if payload['token_type'] != token_type:
                raise jwt.InvalidTokenError('Invalid token type')

            return payload

        except jwt.ExpiredSignatureError:
            raise jwt.InvalidTokenError('Token has expired')
        except jwt.InvalidTokenError as e:
            raise jwt.InvalidTokenError(str(e))

    @staticmethod
    def blacklist_token(token_id, user_id, reason='Logout'):
        """Blacklist a token"""
        # Add to Redis blacklist
        blacklist_key = f'blacklist:{token_id}'
        cache.set(blacklist_key, 'blacklisted', timeout=604800)  # 7 days

        # Update token cache
        token_key = f'token:{token_id}'
        token_data = cache.get(token_key)
        if token_data:
            token_data['is_blacklisted'] = True
            cache.set(token_key, token_data)

        # Store in database for audit
        TokenBlacklist.objects.create(
            token_jti=token_id,
            user_id=user_id,
            blacklist_reason=reason
        )

    @staticmethod
    def is_token_blacklisted(token_id):
        """Check if token is blacklisted"""
        # Check Redis first
        blacklist_key = f'blacklist:{token_id}'
        if cache.get(blacklist_key):
            return True

        # Check database as fallback
        return TokenBlacklist.objects.filter(token_jti=token_id).exists()

