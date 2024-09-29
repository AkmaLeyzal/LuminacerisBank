# services/payment_service/payment/serializers.py

from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ('payment_reference', 'status', 'created_at', 'updated_at')
