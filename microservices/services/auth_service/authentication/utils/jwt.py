# authentication/utils/jwt.py
from typing import Dict, Any, Optional

def generate_jwt_payload(user) -> Dict[str, Any]:
    """Generate JWT payload for user"""
    return {
        'user_id': user.id,
        'email': user.email,
        'username': user.username,
        'roles': [role.name for role in user.roles.all()],
        'permissions': user.get_all_permissions(),
        'status': user.status,
        # Add service-specific claims
        'services': {
            'user_management': True,
            'account': user.is_email_verified,
            'transaction': user.is_email_verified and user.status == 'ACTIVE',
            'payment': user.is_email_verified and user.status == 'ACTIVE'
        }
    }

def get_token_from_request(request) -> Optional[str]:
    """Extract JWT token from request"""
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]
    return None
