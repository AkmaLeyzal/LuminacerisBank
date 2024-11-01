# auth_service/authentication/serializers.py
from rest_framework import serializers
from .models import User, UserSession
from django.contrib.auth import authenticate

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password', 'phone_number']
        extra_kwargs = {
            'password': {'write_only': True},
            'id': {'read_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    device_info = serializers.CharField(required=False)

    def validate(self, data):
        user = authenticate(
            email=data['email'],
            password=data['password']
        )
        if not user:
            raise serializers.ValidationError('Invalid credentials')
        
        if user.is_blocked:
            raise serializers.ValidationError('Account is blocked')
            
        data['user'] = user
        return data

class UserSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSession
        fields = ['device_id', 'device_name', 'last_activity', 'is_active']

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'phone_number', 'is_email_verified', 
                 'is_phone_verified', 'preferred_language', 'last_login']
        read_only_fields = ['id', 'email', 'is_email_verified', 'is_phone_verified']