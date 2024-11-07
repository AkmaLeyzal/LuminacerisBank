# authentication/serializers.py
from rest_framework import serializers
from .models import User, UserSession

class LoginRequestSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=50)
    password = serializers.CharField(max_length=128, write_only=True)
    device_info = serializers.DictField(required=True)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'is_active', 'last_login']
        read_only_fields = ['id', 'last_login']

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSession
        fields = ['session_id', 'device_name', 'device_type', 'ip_address', 
                 'last_activity', 'created_at']

class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return data
    
class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    full_name = serializers.CharField(max_length=255, required=False)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data.get('full_name', '')
        )
        user.status = User.Status.ACTIVE  # Atau PENDING jika ingin verifikasi email
        user.save()
        return user
