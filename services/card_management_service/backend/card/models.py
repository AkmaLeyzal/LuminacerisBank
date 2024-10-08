# services/card_management_service/card/models.py

from django.db import models

class Card(models.Model):
    card_number = models.CharField(max_length=16, unique=True)
    account_id = models.IntegerField()
    card_type = models.CharField(max_length=50, choices=[
        ('Debit', 'Debit'),
        ('Credit', 'Credit'),
        ('Prepaid', 'Prepaid'),
    ])
    cardholder_name = models.CharField(max_length=100)
    expiry_date = models.DateField()
    cvv = models.CharField(max_length=4)
    pin_hash = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=[
        ('Active', 'Active'),
        ('Blocked', 'Blocked'),
        ('Cancelled', 'Cancelled'),
    ], default='Active')
    issued_date = models.DateField(auto_now_add=True)
    limit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
