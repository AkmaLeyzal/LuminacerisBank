from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid
import logging

logger = logging.getLogger(__name__)

class TimestampedModel(models.Model):
    """Abstract base class with timestamp fields"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class BankAccount(TimestampedModel):
    """Model for managing saving accounts"""
    
    class AccountStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        BLOCKED = 'BLOCKED', 'Blocked'
        CLOSED = 'CLOSED', 'Closed'
        DORMANT = 'DORMANT', 'Dormant'
    
    class AccountType(models.TextChoices):
        SAVINGS = 'SAVINGS', 'Savings Account'
    
    class Currency(models.TextChoices):
        IDR = 'IDR', 'Indonesian Rupiah'
        USD = 'USD', 'US Dollar'
        EUR = 'EUR', 'Euro'
        SGD = 'SGD', 'Singapore Dollar'
    
    # Primary Fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.IntegerField(db_index=True)
    account_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Unique account number"
    )
    
    # Account Details
    account_type = models.CharField(
        max_length=50,
        choices=AccountType.choices,
        default=AccountType.SAVINGS
    )
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.IDR
    )
    
    # Balance Information
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00)],
        help_text="Current balance in account"
    )
    available_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00)],
        help_text="Available balance after holds"
    )
    hold_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00)],
        help_text="Amount on hold"
    )
    
    # Limits and Restrictions
    daily_transfer_limit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=50000000.00,  # 50 juta rupiah
        validators=[MinValueValidator(0.00)]
    )
    daily_transfer_used = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00)]
    )
    minimum_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=50000.00,  # 50 ribu rupiah
        validators=[MinValueValidator(0.00)]
    )
    
    # Status Information
    status = models.CharField(
        max_length=20,
        choices=AccountStatus.choices,
        default=AccountStatus.ACTIVE,
        db_index=True
    )
    is_blocked = models.BooleanField(default=False)
    block_reason = models.TextField(null=True, blank=True)
    blocked_at = models.DateTimeField(null=True, blank=True)
    
    # Activity Tracking
    last_activity = models.DateTimeField(default=timezone.now)
    last_transaction_date = models.DateTimeField(null=True, blank=True)
    dormant_since = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    branch_code = models.CharField(max_length=10, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'bank_accounts'
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['account_number']),
            models.Index(fields=['status']),
            models.Index(fields=['last_activity']),
        ]

    def __str__(self):
        return f"{self.account_number} - {self.get_status_display()}"

    def clean(self):
        """Validate model data"""
        if self.balance < self.minimum_balance:
            raise ValidationError({
                'balance': f'Balance cannot be less than minimum balance of {self.minimum_balance}'
            })
        if self.balance < 0:
            raise ValidationError({
                'balance': 'Balance cannot be negative'
            })
        if self.available_balance > self.balance:
            raise ValidationError({
                'available_balance': 'Available balance cannot exceed current balance'
            })

    def save(self, *args, **kwargs):
        """Override save to perform additional operations"""
        self.clean()
        
        # Update available balance
        self.available_balance = self.balance - self.hold_amount
        
        # Check for dormant status
        if self.status == self.AccountStatus.ACTIVE:
            dormant_threshold = timezone.now() - timezone.timedelta(days=365)
            if self.last_activity < dormant_threshold:
                self.status = self.AccountStatus.DORMANT
                self.dormant_since = timezone.now()
                logger.info(f"Account {self.account_number} marked as dormant")
        
        super().save(*args, **kwargs)

class AccountBalanceLog(TimestampedModel):
    """Model for tracking balance changes"""
    
    class ChangeType(models.TextChoices):
        CREDIT = 'CREDIT', 'Credit'
        DEBIT = 'DEBIT', 'Debit'
        ADJUSTMENT = 'ADJUSTMENT', 'Adjustment'
        REVERSAL = 'REVERSAL', 'Reversal'
        HOLD = 'HOLD', 'Hold'
        RELEASE_HOLD = 'RELEASE_HOLD', 'Release Hold'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(
        BankAccount,
        on_delete=models.CASCADE,
        related_name='balance_logs'
    )
    
    # Balance Change Information
    old_balance = models.DecimalField(max_digits=15, decimal_places=2)
    new_balance = models.DecimalField(max_digits=15, decimal_places=2)
    change_amount = models.DecimalField(max_digits=15, decimal_places=2)
    change_type = models.CharField(max_length=50, choices=ChangeType.choices)
    
    # Transaction Details
    transaction_reference = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    
    # Audit Information
    performed_by = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'account_balance_logs'
        indexes = [
            models.Index(fields=['account', 'created_at']),
            models.Index(fields=['transaction_reference']),
            models.Index(fields=['change_type']),
        ]

    def __str__(self):
        return f"{self.account.account_number} - {self.change_type} - {self.change_amount}"

    def save(self, *args, **kwargs):
        """Override save to calculate change amount"""
        if not self.change_amount:
            self.change_amount = self.new_balance - self.old_balance
        super().save(*args, **kwargs)