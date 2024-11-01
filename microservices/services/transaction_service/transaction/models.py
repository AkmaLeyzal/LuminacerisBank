# transaction_service/transaction/models.py
from django.db import models
from django.core.cache import cache
from decimal import Decimal
import uuid

class Transaction(models.Model):
    class TransactionStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        REVERSED = 'REVERSED', 'Reversed'
        BLOCKED = 'BLOCKED', 'Blocked by Fraud Detection'

    transaction_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    reference_number = models.CharField(max_length=50, unique=True)
    sender_account_id = models.IntegerField()
    receiver_account_id = models.IntegerField()
    
    # Amount details
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=6, default=1.0)
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fee_type = models.CharField(max_length=50, null=True)
    
    # Status and routing
    status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING
    )
    description = models.TextField()
    routing_info = models.JSONField(default=dict)
    
    # Timestamps
    scheduled_at = models.DateTimeField(null=True)
    executed_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Security and tracking
    created_by = models.IntegerField()  # User ID who initiated
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255)
    device_id = models.CharField(max_length=255, null=True)
    location = models.JSONField(null=True)
    
    # JWT session tracking
    session_id = models.CharField(max_length=255)
    auth_token_jti = models.CharField(max_length=255)

    class Meta:
        db_table = 'transactions'
        indexes = [
            models.Index(fields=['reference_number']),
            models.Index(fields=['sender_account_id', 'created_at']),
            models.Index(fields=['receiver_account_id', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['scheduled_at']),
        ]

    def save(self, *args, **kwargs):
        """Override save to handle Redis caching"""
        super().save(*args, **kwargs)
        # Cache transaction status
        cache_key = f'transaction:{self.transaction_id}:status'
        cache.set(cache_key, self.status, timeout=3600)  # 1 hour cache
        
        # Update account balance cache if completed
        if self.status == self.TransactionStatus.COMPLETED:
            self._update_account_balance_cache()

    def _update_account_balance_cache(self):
        """Update account balance in Redis cache"""
        # Debit sender account
        sender_key = f'account:{self.sender_account_id}:balance'
        cache.delete(sender_key)  # Invalidate cache
        
        # Credit receiver account
        receiver_key = f'account:{self.receiver_account_id}:balance'
        cache.delete(receiver_key)  # Invalidate cache

class TransactionDetail(models.Model):
    detail_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    notes = models.TextField()
    metadata = models.JSONField(default=dict)
    processing_status = models.CharField(max_length=20)
    error_message = models.TextField(null=True)
    retry_count = models.IntegerField(default=0)
    last_retry_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'transaction_details'
        indexes = [
            models.Index(fields=['transaction', 'processing_status']),
        ]

class TransactionLimitCache:
    """Helper class for managing transaction limits in Redis"""
    
    @staticmethod
    def check_daily_limit(account_id: int, amount: Decimal) -> bool:
        cache_key = f'account:{account_id}:daily_transactions:{datetime.now().date()}'
        
        # Get current daily total from Redis
        daily_total = Decimal(cache.get(cache_key) or 0)
        
        # Check if new transaction would exceed limit
        return daily_total + amount <= Decimal('50000')  # Example limit
    
    @staticmethod
    def update_daily_total(account_id: int, amount: Decimal):
        cache_key = f'account:{account_id}:daily_transactions:{datetime.now().date()}'
        
        # Update daily total in Redis
        daily_total = Decimal(cache.get(cache_key) or 0)
        new_total = daily_total + amount
        
        # Set with expiry at end of day
        seconds_until_midnight = (24 - datetime.now().hour) * 3600
        cache.set(cache_key, str(new_total), timeout=seconds_until_midnight)

class TransactionRateLimit:
    """Helper class for rate limiting transactions"""
    
    @staticmethod
    def check_rate_limit(account_id: int) -> bool:
        cache_key = f'account:{account_id}:transaction_rate'
        
        # Get current count from Redis
        count = cache.get(cache_key) or 0
        
        # Allow max 10 transactions per minute
        return int(count) < 10
    
    @staticmethod
    def increment_counter(account_id: int):
        cache_key = f'account:{account_id}:transaction_rate'
        
        # Increment counter with 1 minute expiry
        cache.set(cache_key, int(cache.get(cache_key) or 0) + 1, timeout=60)

