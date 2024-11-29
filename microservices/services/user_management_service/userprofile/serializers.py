# serializers.py
from rest_framework import serializers
from .models import UserProfile, UserDocument
from .services import UserProfileService

class UserDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDocument
        fields = [
            'document_id',
            'profile',
            'document_type',
            'document_number',
            'expiry_date',
            'verification_status',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['document_id', 'created_at', 'updated_at']

class UserProfileSerializer(serializers.ModelSerializer):
    documents = UserDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'profile_id',
            'user_id',
            'full_name',
            'birth_date',
            'gender',
            'tax_number',
            'phone_number',
            'occupation',
            'monthly_income',
            'documents',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['profile_id', 'created_at', 'updated_at']

    def validate(self, data):
        """Validate user exists in Auth Service"""
        user_id = self.context['request'].parser_context['kwargs'].get('user_id')
        if user_id:
            service = UserProfileService()
            service.validate_user_exists(user_id)
        return data