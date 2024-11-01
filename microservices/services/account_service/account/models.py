# account_service/account/models.py
from django.db import models

class BankAccount(models.Model):
    user_id = models.IntegerField()  # Reference to Auth service User
    account_number = models.CharField(max_length=20, unique=True)
    account_type = models.CharField(max_length=50)  # SAVINGS/CURRENT/DEPOSIT
    currency = models.CharField(max_length=3)
    balance = models.DecimalField(max_digits=15, decimal_places=2)
    available_balance = models.DecimalField(max_digits=15, decimal_places=2)
    hold_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    daily_transfer_limit = models.DecimalField(max_digits=15, decimal_places=2)
    monthly_transfer_limit = models.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=20)  # ACTIVE/DORMANT/BLOCKED
    branch_code = models.CharField(max_length=10)
    last_activity_date = models.DateTimeField()
    opened_at = models.DateTimeField()
    closed_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bank_accounts'
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['account_number']),
            models.Index(fields=['status']),
        ]

class AccountBalanceLog(models.Model):
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)
    old_balance = models.DecimalField(max_digits=15, decimal_places=2)
    new_balance = models.DecimalField(max_digits=15, decimal_places=2)
    change_type = models.CharField(max_length=50)  # CREDIT/DEBIT
    reference_type = models.CharField(max_length=50)
    reference_id = models.CharField(max_length=50)
    description = models.TextField()
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'account_balance_logs'
        indexes = [
            models.Index(fields=['account', 'changed_at']),
            models.Index(fields=['reference_type', 'reference_id']),
        ]

class JointAccountHolder(models.Model):
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)
    user_id = models.IntegerField()
    holder_type = models.CharField(max_length=20)  # PRIMARY/SECONDARY
    access_level = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'joint_account_holders'
        unique_together = ('account', 'user_id')