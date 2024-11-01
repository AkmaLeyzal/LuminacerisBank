from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.cache import cache
from datetime import datetime, timedelta
from django.utils import timezone
import jwt
import uuid

class User(AbstractUser):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        LOCKED = 'LOCKED', 'Locked'
        SUSPENDED = 'SUSPENDED', 'Suspended'
        BLOCKED = 'BLOCKED', 'Blocked'
        PENDING = 'PENDING', 'Pending Verification'
    
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)
    # password_hash dihapus karena duplikat dengan field password dari AbstractUser
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.PENDING
    )
    
    # Security fields
    last_login_ip = models.GenericIPAddressField(null=True)
    last_login_date = models.DateTimeField(null=True)
    failed_login_attempts = models.IntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True)
    password_changed_at = models.DateTimeField(null=True)
    
    # Verification fields
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    email_verification_token = models.CharField(max_length=100, null=True, blank=True)
    phone_verification_code = models.CharField(max_length=6, null=True, blank=True)
    
    # MFA fields
    is_mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=32, null=True, blank=True)
    mfa_backup_codes = models.JSONField(default=list)
    
    # Blocking fields
    is_blocked = models.BooleanField(default=False)
    blocked_at = models.DateTimeField(null=True, blank=True)
    block_reason = models.TextField(null=True, blank=True)
    blocked_by = models.CharField(max_length=50, null=True, blank=True)
    block_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Preferences
    preferred_language = models.CharField(max_length=20, default='en')
    notification_preferences = models.JSONField(default=dict)
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['status']),
            models.Index(fields=['is_blocked']),
            models.Index(fields=['last_activity']),
        ]

    def generate_tokens(self):
        """Generate access and refresh tokens with Redis caching"""
        access_token_id = str(uuid.uuid4())
        refresh_token_id = str(uuid.uuid4())
        
        # Access token payload
        access_payload = {
            'token_type': 'access',
            'user_id': self.id,
            'email': self.email,
            'roles': [role.role_name for role in self.roles.all()],
            'permissions': self.get_all_permissions(),
            'jti': access_token_id,
            'exp': datetime.utcnow() + timedelta(minutes=30)
        }
        
        # Refresh token payload
        refresh_payload = {
            'token_type': 'refresh',
            'user_id': self.id,
            'jti': refresh_token_id,
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
        
        # Cache token data in Redis
        self._cache_token_data(access_token_id, access_payload)
        self._cache_token_data(refresh_token_id, refresh_payload)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 1800  # 30 minutes
        }
        
    def _cache_token_data(self, token_id, payload):
        """Cache token data in Redis"""
        cache_key = f'token:{token_id}'
        cache.set(
            cache_key,
            payload,
            timeout=int((payload['exp'] - datetime.utcnow()).total_seconds())
        )

class TokenBlacklist(models.Model):
    token_jti = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token_type = models.CharField(max_length=50)  # ACCESS/REFRESH
    blacklisted_by = models.CharField(max_length=50)
    blacklist_reason = models.TextField()
    metadata = models.JSONField(default=dict)
    blacklisted_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'token_blacklist'
        indexes = [
            models.Index(fields=['token_jti']),
            models.Index(fields=['user', 'blacklisted_at']),
        ]

    def save(self, *args, **kwargs):
        """Override save to also cache blacklist status"""
        super().save(*args, **kwargs)
        # Cache blacklist status in Redis
        cache_key = f'blacklist:{self.token_jti}'
        cache.set(
            cache_key,
            'blacklisted',
            timeout=int((self.expires_at - datetime.utcnow()).total_seconds())
        )

class UserSession(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    refresh_token_jti = models.CharField(max_length=255)
    access_token_jti = models.CharField(max_length=255)
    
    # Device info
    device_id = models.CharField(max_length=255, null=True)
    device_name = models.CharField(max_length=255, null=True)
    device_type = models.CharField(max_length=50, null=True)
    user_agent = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    location = models.CharField(max_length=255, null=True)
    
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'user_sessions'
        indexes = [
            models.Index(fields=['refresh_token_jti']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['device_id']),
        ]

    def save(self, *args, **kwargs):
        """Override save to cache session data"""
        super().save(*args, **kwargs)
        # Cache session data for quick access
        cache_key = f'session:{self.session_id}'
        session_data = {
            'user_id': self.user_id,
            'device_id': self.device_id,
            'is_active': self.is_active,
            'expires_at': self.expires_at.isoformat()
        }
        cache.set(
            cache_key,
            session_data,
            timeout=int((self.expires_at - datetime.utcnow()).total_seconds())
        )

class SecurityAuditLog(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    event_type = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255)
    event_details = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'security_audit_logs'
        indexes = [
            models.Index(fields=['user', 'event_type']),
            models.Index(fields=['created_at']),
        ]

class Role(models.Model):
    role_name = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    permissions = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'roles'

class UserRole(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    role = models.ForeignKey('Role', on_delete=models.CASCADE)
    assigned_by = models.CharField(max_length=50)
    assigned_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'user_roles'
        unique_together = ('user', 'role')