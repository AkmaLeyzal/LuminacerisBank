# services/account_service/account/models.py

from django.db import models

class Account(models.Model):
    account_number = models.CharField(max_length=20, unique=True)
    user_id = models.IntegerField()
    account_type = models.CharField(max_length=50, choices=[
        ('Savings', 'Savings'),
        ('Checking', 'Checking'),
        ('Deposit', 'Deposit'),
    ])
    balance = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    opened_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('Active', 'Active'),
        ('Closed', 'Closed'),
        ('Suspended', 'Suspended'),
    ], default='Active')
    overdraft_limit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
