# payment_service/payment/models.py
from django.db import models
from django.core.cache import cache
from decimal import Decimal
import uuid

class PaymentTransaction(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'

    payment_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    account_id = models.IntegerField()
    biller_code = models.CharField(max_length=50)
    bill_number = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    admin_fee = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=50)  # PLN/PDAM/BPJS/etc
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    payment_method = models.CharField(max_length=50)
    reference_number = models.CharField(max_length=50, unique=True)
    payment_details = models.JSONField(default=dict)
    
    # Security and tracking
    created_by = models.IntegerField()  # User ID
    ip_address = models.GenericIPAddressField()
    device_id = models.CharField(max_length=255, null=True)
    session_id = models.CharField(max_length=255)
    auth_token_jti = models.CharField(max_length=255)
    
    # Timestamps
    due_date = models.DateTimeField(null=True)
    paid_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment_transactions'
        indexes = [
            models.Index(fields=['reference_number']),
            models.Index(fields=['account_id', 'created_at']),
            models.Index(fields=['payment_status', 'created_at']),
            models.Index(fields=['biller_code', 'bill_number']),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Cache payment status
        cache_key = f'payment:{self.payment_id}:status'
        cache.set(cache_key, self.payment_status, timeout=3600)

class ServiceProvider(models.Model):
    provider_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    provider_name = models.CharField(max_length=100)
    service_type = models.CharField(max_length=50)
    biller_code = models.CharField(max_length=50, unique=True)
    admin_fee_fixed = models.DecimalField(max_digits=10, decimal_places=2)
    admin_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=20)
    config_details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'service_providers'
        indexes = [
            models.Index(fields=['biller_code']),
            models.Index(fields=['service_type']),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Cache provider details
        cache_key = f'provider:{self.biller_code}'
        provider_data = {
            'id': str(self.provider_id),
            'name': self.provider_name,
            'service_type': self.service_type,
            'admin_fee_fixed': str(self.admin_fee_fixed),
            'admin_fee_percentage': str(self.admin_fee_percentage),
            'status': self.status
        }
        cache.set(cache_key, provider_data, timeout=3600)

class PaymentRateLimit:
    """Helper class for rate limiting payments"""
    
    @staticmethod
    def check_rate_limit(account_id: int) -> bool:
        cache_key = f'account:{account_id}:payment_rate'
        count = cache.get(cache_key) or 0
        return int(count) < 5  # Max 5 payments per minute
    
    @staticmethod
    def increment_counter(account_id: int):
        cache_key = f'account:{account_id}:payment_rate'
        cache.set(cache_key, int(cache.get(cache_key) or 0) + 1, timeout=60)

