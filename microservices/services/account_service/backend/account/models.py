from django.db import models

class Account(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('SAV', 'Savings'),
        ('CHK', 'Checking'),
        ('DEP', 'Deposit'),
        ('OTH', 'Other'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('CLOSED', 'Closed'),
        ('SUSPENDED', 'Suspended'),
    ]

    id = models.AutoField(primary_key=True)
    account_number = models.CharField(max_length=20, unique=True)
    user_id = models.IntegerField()  # ID dari User Management Service
    account_type = models.CharField(max_length=3, choices=ACCOUNT_TYPE_CHOICES)
    balance = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    opened_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    overdraft_limit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.account_number
