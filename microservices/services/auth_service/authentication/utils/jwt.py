# utils/jwt.py

from django.conf import settings
from datetime import timedelta
from django.utils import timezone
import jwt
import uuid
import json
import pytz

timezone.activate(pytz.timezone('Asia/Jakarta'))

def generate_jwt_payload(user):
    """Generate JWT payload with proper UUID serialization"""
    return {
        'user_id': str(user.id),  # Convert UUID to string
        'email': user.email,
        'username': user.username,
        'roles': [str(role.id) for role in user.roles.all()],  # Convert role UUIDs to strings
        'permissions': user.get_all_permissions(),
        'status': user.status,
        'is_active': user.is_active,
        'is_email_verified': user.is_email_verified,
        'exp': timezone.now() + timedelta(minutes=5)
    }

def encode_auth_token(payload):
    """Encode auth token ensuring all UUIDs are strings"""
    try:
        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm='HS256'
        )
    except Exception as e:
        raise Exception(f"Error encoding JWT token: {str(e)}")

def decode_auth_token(token):
    """Decode auth token"""
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=['HS256']
        )
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")

def get_token_from_request(request):
    """Extract token from request header"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise Exception("No valid authorization header")
    return auth_header.split(' ')[1]

class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for UUID objects"""
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)