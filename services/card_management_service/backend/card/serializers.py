# services/card_management_service/card/serializers.py

from rest_framework import serializers
from .models import Card

class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = '__all__'
        read_only_fields = ('card_number', 'status', 'issued_date', 'created_at', 'updated_at')
        extra_kwargs = {
            'cvv': {'write_only': True},
            'pin_hash': {'write_only': True},
        }
