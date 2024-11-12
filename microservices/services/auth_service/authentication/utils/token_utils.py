# authentication/utils/token_utils.py

from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from typing import Dict, Optional
import jwt
import uuid
import logging

logger = logging.getLogger(__name__)

class TokenManager:
    @staticmethod
    def generate_tokens(user_id: int, user_data: Dict) -> Dict:
        """Generate new access and refresh tokens"""
        access_token_id = str(uuid.uuid4())
        refresh_token_id = str(uuid.uuid4())
        
        # Access token payload
        access_payload = {
            'token_type': 'access',
            'user_id': user_id,
            'jti': access_token_id,
            'user_data': user_data,
            'exp': datetime.utcnow() + timedelta(minutes=30)
        }
        
        # Refresh token payload
        refresh_payload = {
            'token_type': 'refresh',
            'user_id': user_id,
            'jti': refresh_token_id,
            'exp': datetime.utcnow() + timedelta(days=7)
        }
        
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

    @staticmethod
    def _cache_token_data(token_id: str, payload: Dict):
        """Cache token data in Redis"""
        cache_key = f'token:{token_id}'
        cache.set(
            cache_key,
            payload,
            timeout=int((payload['exp'] - datetime.utcnow()).total_seconds())
        )

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
                'roles': [role.name for role in user.roles.all()],
                'permissions': user.get_all_permissions()
            }
            
            access_token_id = str(uuid.uuid4())
            access_payload = {
                'token_type': 'access',
                'user_id': user_id,
                'jti': access_token_id,
                'user_data': user_data,
                'exp': datetime.utcnow() + timedelta(minutes=30)
            }
            
            access_token = jwt.encode(
                access_payload,
                settings.JWT_SECRET_KEY,
                algorithm='HS256'
            )
            
            # Cache new token data
            TokenManager._cache_token_data(access_token_id, access_payload)
            
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
    def blacklist_token(token_jti: str, user_id: int, reason: str, blacklisted_by: str):
        """Add token to blacklist"""
        from authentication.models import TokenBlacklist
        
        # Add to database
        TokenBlacklist.objects.create(
            token_jti=token_jti,
            user_id=user_id,
            blacklist_reason=reason,
            blacklisted_by=blacklisted_by,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        # Add to cache
        cache_key = f'blacklist:{token_jti}'
        cache.set(cache_key, True, timeout=7*24*60*60)  # 7 days
        
        return True