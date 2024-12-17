# authentication/utils/token_utils.py

from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from typing import Dict, Optional
import jwt
import uuid
import json
import logging

logger = logging.getLogger(__name__)

class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, timezone.datetime):
            return obj.isoformat()
        return super().default(obj)

def serialize_payload(payload: Dict) -> Dict:
    """Serialize payload to ensure all objects are JSON serializable"""
    return json.loads(json.dumps(payload, cls=UUIDEncoder))

class TokenManager:
    @staticmethod
    def generate_tokens(user_id: str, user_data: Dict) -> Dict:
        """Generate new access and refresh tokens"""
        try:
            access_token_id = str(uuid.uuid4())
            refresh_token_id = str(uuid.uuid4())
            
            # Convert user_id to string if it's UUID
            user_id = str(user_id)
            
            # Serialize user_data to handle UUID
            serialized_user_data = serialize_payload(user_data)
            
            # Access token payload
            access_payload = {
                'token_type': 'access',
                'user_id': user_id,
                'jti': access_token_id,
                'user_data': serialized_user_data,
                'exp': timezone.now() + timedelta(minutes=30)
            }
            
            # Refresh token payload
            refresh_payload = {
                'token_type': 'refresh',
                'user_id': user_id,
                'jti': refresh_token_id,
                'exp': timezone.now() + timedelta(days=7)
            }
            
            # Serialize payloads before encoding
            access_payload = serialize_payload(access_payload)
            refresh_payload = serialize_payload(refresh_payload)
            
            # Generate JWT tokens
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
            
            # Cache token data
            TokenManager._cache_token_data(access_token_id, access_payload)
            TokenManager._cache_token_data(refresh_token_id, refresh_payload)
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'access_token_id': access_token_id,
                'refresh_token_id': refresh_token_id,
                'expires_in': 1800  # 30 minutes
            }
        except Exception as e:
            logger.error(f"Token generation failed: {str(e)}")
            raise ValueError(f"Token generation failed: {str(e)}")

    @staticmethod
    def _cache_token_data(token_id: str, payload: Dict):
        """Cache token data in Redis"""
        try:
            cache_key = f'token:{token_id}'
            serialized_payload = serialize_payload(payload)
            expiry = payload['exp']
            if isinstance(expiry, str):
                expiry = timezone.datetime.fromisoformat(expiry)
            timeout = int((expiry - timezone.now()).total_seconds())
            cache.set(cache_key, serialized_payload, timeout=timeout)
        except Exception as e:
            logger.error(f"Token caching failed: {str(e)}")
            raise ValueError(f"Token caching failed: {str(e)}")

    @staticmethod
    def verify_token(token: str, token_type: str = 'access') -> Optional[Dict]:
        """Verify JWT token and check blacklist"""
        try:
            secret_key = settings.JWT_SECRET_KEY if token_type == 'access' else settings.JWT_REFRESH_SECRET_KEY
            decoded_token = jwt.decode(token, secret_key, algorithms=['HS256'])
            
            # Validate token type
            if decoded_token.get('token_type') != token_type:
                raise ValueError('Invalid token type')
            
            # Check blacklist
            if TokenBlacklistManager.is_blacklisted(decoded_token['jti']):
                raise ValueError('Token has been blacklisted')
            
            # Verify cached token
            cache_key = f'token:{decoded_token["jti"]}'
            cached_token = cache.get(cache_key)
            
            if not cached_token:
                raise ValueError('Token not found in cache')
            
            return decoded_token
            
        except jwt.ExpiredSignatureError:
            raise ValueError('Token has expired')
        except jwt.InvalidTokenError:
            raise ValueError('Invalid token')
        except Exception as e:
            logger.error(f'Token verification failed: {str(e)}')
            raise ValueError(f'Token verification failed: {str(e)}')

    @staticmethod
    def refresh_access_token(refresh_token: str) -> Dict:
        """Generate new access token using refresh token"""
        try:
            decoded_refresh = TokenManager.verify_token(refresh_token, 'refresh')
            user_id = decoded_refresh['user_id']
            
            from authentication.models import User
            user = User.objects.get(id=user_id)
            
            # Generate new access token
            user_data = {
                'email': user.email,
                'username': user.username,
                'roles': [{'id': str(role.id), 'name': role.name} for role in user.roles.all()],
                'permissions': user.get_all_permissions()
            }
            
            access_token_id = str(uuid.uuid4())
            access_payload = {
                'token_type': 'access',
                'user_id': str(user.id),
                'jti': access_token_id,
                'user_data': user_data,
                'exp': timezone.now() + timedelta(minutes=30)
            }
            
            # Serialize payload before encoding
            serialized_payload = serialize_payload(access_payload)
            
            access_token = jwt.encode(
                serialized_payload,
                settings.JWT_SECRET_KEY,
                algorithm='HS256'
            )
            
            # Cache new token data
            TokenManager._cache_token_data(access_token_id, serialized_payload)
            
            return {
                'access_token': access_token,
                'access_token_id': access_token_id,
                'expires_in': 1800
            }
            
        except Exception as e:
            logger.error(f'Token refresh failed: {str(e)}')
            raise ValueError(f'Token refresh failed: {str(e)}')

class TokenBlacklistManager:
    @staticmethod
    def blacklist_token(token_jti: str, user_id: str, reason: str, blacklisted_by: str):
        """Add token to blacklist"""
        try:
            from authentication.models import TokenBlacklist
            
            # Add to database
            TokenBlacklist.objects.create(
                token_jti=token_jti,
                user_id=user_id,  # UUID will be handled by the model
                blacklist_reason=reason,
                blacklisted_by=blacklisted_by,
                expires_at=timezone.now() + timedelta(days=7)
            )
            
            # Add to cache
            cache_key = f'blacklist:{token_jti}'
            cache.set(cache_key, True, timeout=7*24*60*60)  # 7 days
            
            return True
        except Exception as e:
            logger.error(f"Token blacklisting failed: {str(e)}")
            raise ValueError(f"Token blacklisting failed: {str(e)}")
    
    @staticmethod
    def is_blacklisted(token_jti: str) -> bool:
        """Check if token is blacklisted"""
        try:
            cache_key = f'blacklist:{token_jti}'
            is_blacklisted = cache.get(cache_key)
            
            if is_blacklisted is None:
                from authentication.models import TokenBlacklist
                is_blacklisted = TokenBlacklist.objects.filter(token_jti=token_jti).exists()
                cache.set(cache_key, is_blacklisted, timeout=7*24*60*60)  # 7 days
            
            return is_blacklisted
        except Exception as e:
            logger.error(f"Blacklist check failed: {str(e)}")
            return True  # Fail safe: treat as blacklisted if check fails