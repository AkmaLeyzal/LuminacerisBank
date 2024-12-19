# services/transaction_service/transaction/serializers.py
from rest_framework import serializers
from django.utils import timezone
from .models import Transaction, TransactionDetail
from decimal import Decimal

class TransactionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionDetail
        fields = [
            'detail_id',
            'processing_status',
            'notes',
            'metadata',
            'error_message',
            'retry_count',
            'last_retry_at',
            'created_at'
        ]
        read_only_fields = ['detail_id', 'created_at']

class TransactionSerializer(serializers.ModelSerializer):
    details = TransactionDetailSerializer(many=True, read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'transaction_id',
            'reference_number',
            'transaction_type',
            'sender_account_id',
            'receiver_account_id',
            'amount',
            'currency',
            'exchange_rate',
            'fee_amount',
            'fee_type',
            'status',
            'description',
            'routing_info',
            'original_transaction',
            'scheduled_at',
            'executed_at',
            'created_at',
            'updated_at',
            'details',
            'is_active'
        ]
        read_only_fields = [
            'transaction_id',
            'reference_number',
            'fee_amount',
            'fee_type',
            'status',
            'executed_at',
            'created_at',
            'updated_at',
            'is_active'
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive")
        if value > Decimal('1000000000'):
            raise serializers.ValidationError("Amount exceeds maximum limit")
        return value

    def validate_scheduled_at(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError("Scheduled time must be in the future")
        return value

class TransferRequestSerializer(serializers.Serializer):
    transaction_type = serializers.ChoiceField(
        choices=Transaction.TransactionType.choices,
        default=Transaction.TransactionType.TRANSFER
    )
    receiver_account_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    currency = serializers.CharField(max_length=3)
    description = serializers.CharField(required=False, allow_blank=True, max_length=500)
    scheduled_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Transfer amount must be positive")
        if value > Decimal('1000000000'):
            raise serializers.ValidationError("Amount exceeds maximum limit")
        return value

    def validate_scheduled_at(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError("Scheduled time must be in the future")
        return value

    def validate(self, data):
        if data['receiver_account_id'] == self.context.get('sender_account_id'):
            raise serializers.ValidationError(
                "Cannot transfer to the same account"
            )
        return data

class TransactionStatusSerializer(serializers.Serializer):
    transaction_id = serializers.UUIDField()
    reference_number = serializers.CharField()
    status = serializers.ChoiceField(choices=Transaction.TransactionStatus.choices)
    transaction_type = serializers.ChoiceField(choices=Transaction.TransactionType.choices)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    currency = serializers.CharField()
    fee_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    executed_at = serializers.DateTimeField(allow_null=True)
    error_message = serializers.CharField(allow_null=True, required=False)
    processing_status = serializers.CharField(source='details.processing_status', allow_null=True)

class TransactionListRequestSerializer(serializers.Serializer):
    account_id = serializers.UUIDField(required=False)
    transaction_type = serializers.ChoiceField(
        choices=Transaction.TransactionType.choices,
        required=False
    )
    status = serializers.ChoiceField(
        choices=Transaction.TransactionStatus.choices,
        required=False
    )
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    min_amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False
    )
    max_amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False
    )
    currency = serializers.CharField(max_length=3, required=False, default='IDR')
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=20)

    def validate(self, data):
        if data.get('end_date') and data.get('start_date'):
            if data['end_date'] < data['start_date']:
                raise serializers.ValidationError(
                    "End date must be after start date"
                )
        
        if data.get('max_amount') and data.get('min_amount'):
            if data['max_amount'] < data['min_amount']:
                raise serializers.ValidationError(
                    "Maximum amount must be greater than minimum amount"
                )
        return data

class ReverseTransactionSerializer(serializers.Serializer):
    transaction_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=500)
    reversal_amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False
    )

    def validate_reversal_amount(self, value):
        original_transaction = self.context.get('original_transaction')
        if value and value > original_transaction.amount:
            raise serializers.ValidationError(
                "Reversal amount cannot exceed original transaction amount"
            )
        return value

class AccountInfoSerializer(serializers.Serializer):
    """Serializer for Account Service response"""
    account_id = serializers.UUIDField()
    account_number = serializers.CharField()
    account_type = serializers.CharField()
    currency = serializers.CharField()
    balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    status = serializers.CharField()
    daily_limit = serializers.DecimalField(max_digits=15, decimal_places=2)
    is_active = serializers.BooleanField()