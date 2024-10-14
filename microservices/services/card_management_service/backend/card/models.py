from django.db import models
from django.contrib.auth.hashers import make_password

class Card(models.Model):
    CARD_TYPE_CHOICES = [
        ('DEBIT', 'Debit'),
        ('CREDIT', 'Credit'),
        ('PREPAID', 'Prepaid'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('BLOCKED', 'Blocked'),
        ('CANCELLED', 'Cancelled'),
    ]

    id = models.AutoField(primary_key=True)
    card_number = models.CharField(max_length=16, unique=True)
    account_id = models.IntegerField()  # ID dari Account Service
    card_type = models.CharField(max_length=7, choices=CARD_TYPE_CHOICES)
    cardholder_name = models.CharField(max_length=255)
    expiry_date = models.DateField()
    cvv = models.CharField(max_length=4)
    pin_hash = models.CharField(max_length=128)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    issued_date = models.DateField(auto_now_add=True)
    limit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)  # Untuk kartu kredit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Hash CVV dan PIN sebelum menyimpan
        if not self.pk:
            self.cvv = make_password(self.cvv)
            self.pin_hash = make_password(self.pin_hash)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.card_number
