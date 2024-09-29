# services/transaction_service/transaction/models.py

from django.db import models

class Transaction(models.Model):
    transaction_reference = models.CharField(max_length=100, unique=True)
    from_account_id = models.IntegerField()
    to_account_id = models.IntegerField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3)
    transaction_type = models.CharField(max_length=50, choices=[
        ('Transfer', 'Transfer'),
        ('Deposit', 'Deposit'),
        ('Withdrawal', 'Withdrawal'),
        ('Payment', 'Payment'),
    ])
    transaction_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
    ], default='Pending')
    description = models.TextField(null=True, blank=True)
    fee = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
