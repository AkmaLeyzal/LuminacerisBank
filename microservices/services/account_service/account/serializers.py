# accounts/serializers.py

from rest_framework import serializers
from django.conf import settings
from .models import BankAccount, AccountBalanceLog
from typing import Dict, Any

class BankAccountSerializer(serializers.ModelSerializer):
    """Serializer for BankAccount model"""
    
    class Meta:
        model = BankAccount
        fields = [
            'id', 'user_id', 'account_number', 'account_type',
            'currency', 'balance', 'available_balance', 'hold_amount',
            'status', 'last_activity', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'account_number', 'balance', 'available_balance',
            'hold_amount', 'last_activity', 'created_at', 'updated_at'
        ]

class AccountCreateSerializer(serializers.Serializer):
    """Serializer for account creation"""
    
    user_id = serializers.IntegerField()
    account_type = serializers.ChoiceField(choices=BankAccount.AccountType.choices)
    currency = serializers.ChoiceField(choices=BankAccount.Currency.choices)
    initial_deposit = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=settings.ACCOUNT_LIMITS['MIN_BALANCE']
    )

class AccountStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating account status"""
    
    status = serializers.ChoiceField(choices=BankAccount.AccountStatus.choices)
    reason = serializers.CharField(max_length=255, required=False)

class AccountHoldAmountSerializer(serializers.Serializer):
    """Serializer for hold amount operations"""
    
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    reason = serializers.CharField(max_length=255)
    reference = serializers.CharField(max_length=100)