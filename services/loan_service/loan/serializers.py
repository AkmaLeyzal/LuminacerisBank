# services/loan_service/loan/serializers.py

from rest_framework import serializers
from .models import LoanApplication
import uuid

class LoanApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanApplication
        fields = '__all__'
        read_only_fields = ('loan_reference', 'status', 'application_date', 'approval_date', 'created_at', 'updated_at')

    def create(self, validated_data):
        validated_data['loan_reference'] = str(uuid.uuid4())
        # Hitung monthly_payment berdasarkan principal_amount, interest_rate, dan term_months
        principal = validated_data['principal_amount']
        rate = validated_data['interest_rate'] / 100 / 12
        term = validated_data['term_months']
        if rate > 0:
            payment = principal * (rate * (1 + rate) ** term) / ((1 + rate) ** term - 1)
        else:
            payment = principal / term
        validated_data['monthly_payment'] = round(payment, 2)
        return super().create(validated_data)
