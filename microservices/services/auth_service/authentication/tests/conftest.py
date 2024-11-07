# authentication/tests/conftest.py
import pytest
from rest_framework.test import APIClient
from django.core.cache import cache
from authentication.models import User, Role
from authentication.services.token_service import TokenService
import jwt
from datetime import datetime, timedelta

@pytest.fixture(autouse=True)
def clean_cache():
    """Clean Redis cache before each test"""
    cache.clear()
    yield
    cache.clear()

@pytest.fixture
def api_client():
    """Return Django REST framework API client"""
    return APIClient()

@pytest.fixture
def admin_role():
    """Create and return admin role"""
    return Role.objects.create(
        name='ADMIN',
        description='Administrator role',
        permissions={
            'users': ['create', 'read', 'update', 'delete'],
            'roles': ['create', 'read', 'update', 'delete'],
            'security': ['manage']
        }
    )

@pytest.fixture
def user_role():
    """Create and return regular user role"""
    return Role.objects.create(
        name='USER',
        description='Regular user role',
        permissions={
            'users': ['read'],
            'roles': ['read']
        }
    )

@pytest.fixture
def admin_user(admin_role):
    """Create and return admin user"""
    user = User.objects.create(
        username='admin',
        email='admin@example.com',
        password='Admin@123',
        is_staff=True,
        is_superuser=True,
        status=User.Status.ACTIVE,
        is_email_verified=True
    )
    user.roles.add(admin_role)
    return user

@pytest.fixture
def regular_user(user_role):
    """Create and return regular user"""
    user = User.objects.create(
        username='user',
        email='user@example.com',
        password='User@123',
        status=User.Status.ACTIVE,
        is_email_verified=True
    )
    user.roles.add(user_role)
    return user

@pytest.fixture
def access_token(regular_user):
    """Generate and return access token for regular user"""
    return TokenService.generate_token_pair(regular_user)['access_token']

@pytest.fixture
def admin_token(admin_user):
    """Generate and return access token for admin user"""
    return TokenService.generate_token_pair(admin_user)['access_token']


