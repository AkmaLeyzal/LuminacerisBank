# authentication/serializers.py

from rest_framework import serializers
from .models import User, Role

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('id', 'name', 'permissions')

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'username', 'password', 'confirm_password',
            'full_name', 'phone_number'
        )
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'full_name': {'required': True}
        }

    def validate(self, data):
        # Validate password match
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({
                "password": "Passwords don't match."
            })

        # Validate email
        email = data.get('email', '').lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({
                "email": "This email is already registered."
            })

        # Validate username
        username = data.get('username', '').lower()
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({
                "username": "This username is already taken."
            })

        # Remove confirm_password from the data
        if 'confirm_password' in data:
            del data['confirm_password']

        return data

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    device_id = serializers.CharField(required=False)
    device_name = serializers.CharField(required=False)
    device_type = serializers.CharField(required=False)

class TokenResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    expires_in = serializers.IntegerField()
    token_type = serializers.CharField(default='Bearer')

class UserResponseSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(many=True, read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'full_name', 'roles',
            'permissions', 'status', 'is_email_verified',
            'last_login_date', 'phone_number'
        )

    def get_permissions(self, obj):
        return obj.get_all_permissions()

class LoginResponseSerializer(serializers.Serializer):
    user = UserResponseSerializer()
    tokens = TokenResponseSerializer()
    message = serializers.CharField()

class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)

class PasswordResetSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField()

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                "password": "Passwords don't match."
            })
        return data

class TokenRefreshSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

class TokenRefreshResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    expires_in = serializers.IntegerField()

class UserVerificationStatusSerializer(serializers.ModelSerializer):
    """Serializer for user verification status"""
    is_verified = serializers.SerializerMethodField()
    verification_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'status', 
            'is_verified', 'verification_status',
            'is_email_verified', 'is_phone_verified',
            'last_login_ip', 'last_login_date',
            'roles', 'created_at'
        ]
        read_only_fields = fields

    def get_is_verified(self, obj):
        """Check if user is fully verified"""
        return obj.is_email_verified and obj.status == User.Status.ACTIVE

    def get_verification_status(self, obj):
        """Get detailed verification status"""
        status = {
            'email': obj.is_email_verified,
            'phone': obj.is_phone_verified,
            'account': obj.status == User.Status.ACTIVE,
            'required_steps': []
        }

        # Add required verification steps
        if not obj.is_email_verified:
            status['required_steps'].append('EMAIL_VERIFICATION')
        if not obj.is_phone_verified:
            status['required_steps'].append('PHONE_VERIFICATION')
        if obj.status != User.Status.ACTIVE:
            status['required_steps'].append('ACCOUNT_ACTIVATION')

        return status