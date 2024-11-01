# card_management_service/card/models.py
from django.db import models
from django.core.cache import cache
from decimal import Decimal
import uuid

class Card(models.Model):
    class CardStatus(models.TextChoices):
        INACTIVE = 'INACTIVE', 'Inactive'
        ACTIVE = 'ACTIVE', 'Active'
        BLOCKED = 'BLOCKED', 'Blocked'
        EXPIRED = 'EXPIRED', 'Expired'
        SUSPENDED = 'SUSPENDED', 'Suspended'

    class CardType(models.TextChoices):
        DEBIT = 'DEBIT', 'Debit Card'
        CREDIT = 'CREDIT', 'Credit Card'

    class CardNetwork(models.TextChoices):
        VISA = 'VISA', 'Visa'
        MASTERCARD = 'MASTERCARD', 'Mastercard'

    card_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    account_id = models.IntegerField()
    card_number = models.CharField(max_length=16, unique=True)
    card_type = models.CharField(max_length=50, choices=CardType.choices)
    card_network = models.CharField(max_length=20, choices=CardNetwork.choices)
    cardholder_name = models.CharField(max_length=255)
    expiry_date = models.DateField()
    cvv = models.CharField(max_length=4)
    pin_hash = models.CharField(max_length=255)
    
    # Limits
    daily_limit = models.DecimalField(max_digits=15, decimal_places=2)
    monthly_limit = models.DecimalField(max_digits=15, decimal_places=2)
    current_daily_usage = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    current_monthly_usage = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Features
    is_contactless = models.BooleanField(default=True)
    is_online_enabled = models.BooleanField(default=True)
    is_international_enabled = models.BooleanField(default=False)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=CardStatus.choices,
        default=CardStatus.INACTIVE
    )
    activated_date = models.DateTimeField(null=True)
    blocked_at = models.DateTimeField(null=True)
    block_reason = models.TextField(null=True)
    last_used_at = models.DateTimeField(null=True)
    
    # Security
    security_level = models.IntegerField(default=1)
    failed_pin_attempts = models.IntegerField(default=0)
    last_failed_attempt = models.DateTimeField(null=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cards'
        indexes = [
            models.Index(fields=['card_number']),
            models.Index(fields=['account_id']),
            models.Index(fields=['status']),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Cache card status and limits
        self._update_card_cache()

    def _update_card_cache(self):
        """Update card information in Redis cache"""
        cache_key = f'card:{self.card_number}'
        card_data = {
            'status': self.status,
            'daily_limit': str(self.daily_limit),
            'monthly_limit': str(self.monthly_limit),
            'current_daily_usage': str(self.current_daily_usage),
            'current_monthly_usage': str(self.current_monthly_usage),
            'is_online_enabled': self.is_online_enabled,
            'is_international_enabled': self.is_international_enabled,
            'security_level': self.security_level
        }
        cache.set(cache_key, card_data, timeout=3600)  # 1 hour cache

class CardTransaction(models.Model):
    class TransactionStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        AUTHORIZED = 'AUTHORIZED', 'Authorized'
        COMPLETED = 'COMPLETED', 'Completed'
        DECLINED = 'DECLINED', 'Declined'
        REVERSED = 'REVERSED', 'Reversed'
        REFUNDED = 'REFUNDED', 'Refunded'

    transaction_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    merchant_name = models.CharField(max_length=255)
    merchant_category_code = models.CharField(max_length=4)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3)
    
    # Transaction details
    transaction_type = models.CharField(max_length=50)
    authorization_code = models.CharField(max_length=20)
    reference_number = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING
    )
    
    # Location and type
    location = models.CharField(max_length=100)
    is_international = models.BooleanField()
    is_online = models.BooleanField()
    
    # Security
    ip_address = models.GenericIPAddressField(null=True)
    device_fingerprint = models.CharField(max_length=255, null=True)
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    
    # Timestamps
    transaction_date = models.DateTimeField()
    cleared_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'card_transactions'
        indexes = [
            models.Index(fields=['card', 'transaction_date']),
            models.Index(fields=['reference_number']),
            models.Index(fields=['status']),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update usage in Redis
        self._update_usage_cache()

    def _update_usage_cache(self):
        """Update card usage in Redis"""
        if self.status == self.TransactionStatus.COMPLETED:
            # Update daily usage
            daily_key = f'card:{self.card.card_number}:daily_usage:{datetime.now().date()}'
            cache.incr(daily_key, int(self.amount * 100))  # Store as cents
            cache.expire(daily_key, 24 * 3600)  # Expire in 24 hours

            # Update monthly usage
            monthly_key = f'card:{self.card.card_number}:monthly_usage:{datetime.now().strftime("%Y-%m")}'
            cache.incr(monthly_key, int(self.amount * 100))
            cache.expire(monthly_key, 31 * 24 * 3600)  # Expire in 31 days

class CardSecurityService:
    """Helper class for card security features"""
    
    @staticmethod
    def check_transaction_limit(card_number: str, amount: Decimal) -> bool:
        cache_key = f'card:{card_number}'
        card_data = cache.get(cache_key)
        
        if not card_data:
            return False
            
        daily_usage = Decimal(card_data['current_daily_usage'])
        monthly_usage = Decimal(card_data['current_monthly_usage'])
        
        return (daily_usage + amount <= Decimal(card_data['daily_limit']) and
                monthly_usage + amount <= Decimal(card_data['monthly_limit']))

    @staticmethod
    def record_failed_attempt(card_number: str):
        """Record failed PIN attempt"""
        cache_key = f'card:{card_number}:failed_attempts'
        attempts = cache.get(cache_key) or 0
        
        if int(attempts) >= 3:
            # Auto-block card
            Card.objects.filter(card_number=card_number).update(
                status=Card.CardStatus.BLOCKED,
                blocked_at=timezone.now(),
                block_reason='Exceeded maximum PIN attempts'
            )
        else:
            cache.set(cache_key, int(attempts) + 1, timeout=1800)  # 30 minutes

