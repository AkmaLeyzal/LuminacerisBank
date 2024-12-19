# transaction/models.py
from django.db import models
from django.core.cache import cache
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid
from datetime import datetime

class Transaction(models.Model):
    class TransactionStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        REVERSED = 'REVERSED', 'Reversed'
        BLOCKED = 'BLOCKED', 'Blocked by Fraud Detection'
        CANCELLED = 'CANCELLED', 'Cancelled'

    class TransactionType(models.TextChoices):
        TRANSFER = 'TRANSFER', 'Transfer'
        PAYMENT = 'PAYMENT', 'Payment'
        WITHDRAWAL = 'WITHDRAWAL', 'Withdrawal'
        DEPOSIT = 'DEPOSIT', 'Deposit'
        REVERSAL = 'REVERSAL', 'Reversal'

    # Primary Fields
    transaction_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_number = models.CharField(max_length=50, unique=True)
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        default=TransactionType.TRANSFER
    )

    # Account Information
    sender_account_id = models.UUIDField(db_index=True)
    receiver_account_id = models.UUIDField(db_index=True)
    
    # Amount and Currency Information
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(max_length=3)
    exchange_rate = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=1.0,
        validators=[MinValueValidator(Decimal('0.000001'))]
    )
    
    # Fee Information
    fee_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    fee_type = models.CharField(max_length=50, null=True)
    
    # Status and Transaction Information
    status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        db_index=True
    )
    description = models.TextField(blank=True)
    routing_info = models.JSONField(default=dict)
    
    # Related Transaction (for reversals)
    original_transaction = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reversals'
    )
    
    # Scheduling Information
    scheduled_at = models.DateTimeField(null=True, blank=True, db_index=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Security and Tracking Information
    created_by = models.UUIDField()  # User ID who initiated
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255)
    device_id = models.CharField(max_length=255, null=True, blank=True)
    location = models.JSONField(null=True, blank=True)
    
    # Session Tracking
    session_id = models.CharField(max_length=255)
    auth_token_jti = models.CharField(max_length=255)

    # Soft Delete
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'transactions'
        indexes = [
            models.Index(fields=['reference_number']),
            models.Index(fields=['sender_account_id', 'created_at']),
            models.Index(fields=['receiver_account_id', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['is_active']),
        ]

    def save(self, *args, **kwargs):
        """Override save to handle Redis caching and validation"""
        if self.amount <= 0:
            raise ValueError("Transaction amount must be positive")
            
        super().save(*args, **kwargs)
        
        # Cache transaction status
        cache_key = f'transaction:{self.transaction_id}:status'
        cache.set(cache_key, self.status, timeout=3600)  # 1 hour cache
        
        # Update account balance cache if completed
        if self.status == self.TransactionStatus.COMPLETED:
            self._update_account_balance_cache()

    def soft_delete(self):
        """Soft delete the transaction"""
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save()

    def _update_account_balance_cache(self):
        """Update account balance in Redis cache"""
        # Invalidate sender account balance cache
        sender_key = f'account:{self.sender_account_id}:balance'
        cache.delete(sender_key)
        
        # Invalidate receiver account balance cache
        receiver_key = f'account:{self.receiver_account_id}:balance'
        cache.delete(receiver_key)

class TransactionDetail(models.Model):
    class ProcessingStatus(models.TextChoices):
        INITIATED = 'INITIATED', 'Initiated'
        VALIDATING = 'VALIDATING', 'Validating'
        FRAUD_CHECKING = 'FRAUD_CHECKING', 'Fraud Checking'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    detail_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='details'
    )
    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.INITIATED
    )
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    error_message = models.TextField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    last_retry_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'transaction_details'
        indexes = [
            models.Index(fields=['transaction', 'processing_status']),
            models.Index(fields=['created_at']),
        ]

class TransactionLimitCache:
    """Helper class for managing transaction limits in Redis"""
    
    @staticmethod
    def get_daily_limit(account_id: uuid.UUID) -> Decimal:
        """Get account daily limit from cache or default"""
        cache_key = f'account:{account_id}:daily_limit'
        limit = cache.get(cache_key)
        return Decimal(limit) if limit else Decimal('50000.00')  # Default limit
    
    @staticmethod
    def check_daily_limit(account_id: uuid.UUID, amount: Decimal) -> bool:
        """Check if transaction amount is within daily limit"""
        cache_key = f'account:{account_id}:daily_transactions:{datetime.now().date()}'
        
        # Get current daily total from Redis
        daily_total = Decimal(cache.get(cache_key) or '0')
        daily_limit = TransactionLimitCache.get_daily_limit(account_id)
        
        return daily_total + amount <= daily_limit
    
    @staticmethod
    def update_daily_total(account_id: uuid.UUID, amount: Decimal):
        """Update daily transaction total in Redis"""
        cache_key = f'account:{account_id}:daily_transactions:{datetime.now().date()}'
        
        # Update daily total in Redis
        daily_total = Decimal(cache.get(cache_key) or '0')
        new_total = daily_total + amount
        
        # Set with expiry at end of day
        seconds_until_midnight = (24 - datetime.now().hour) * 3600
        cache.set(cache_key, str(new_total), timeout=seconds_until_midnight)

class TransactionRateLimit:
    """Helper class for rate limiting transactions"""
    
    MAX_TRANSACTIONS_PER_MINUTE = 10
    RATE_LIMIT_DURATION = 60  # seconds
    
    @staticmethod
    def check_rate_limit(account_id: uuid.UUID) -> bool:
        """Check if account has exceeded transaction rate limit"""
        cache_key = f'account:{account_id}:transaction_rate'
        
        # Get current count from Redis
        count = cache.get(cache_key) or 0
        
        return int(count) < TransactionRateLimit.MAX_TRANSACTIONS_PER_MINUTE
    
    @staticmethod
    def increment_counter(account_id: uuid.UUID):
        """Increment transaction counter for rate limiting"""
        cache_key = f'account:{account_id}:transaction_rate'
        
        # Increment counter with expiry
        pipe = cache.client.pipeline()
        pipe.incr(cache_key)
        pipe.expire(cache_key, TransactionRateLimit.RATE_LIMIT_DURATION)
        pipe.execute()