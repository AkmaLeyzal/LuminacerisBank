# services/loan_service/loan/models.py

from django.db import models

class LoanApplication(models.Model):
    loan_reference = models.CharField(max_length=100, unique=True)
    user_id = models.IntegerField()
    loan_type = models.CharField(max_length=50, choices=[
        ('Personal', 'Personal'),
        ('Mortgage', 'Mortgage'),
        ('Auto', 'Auto'),
        ('Education', 'Education'),
    ])
    principal_amount = models.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term_months = models.IntegerField()
    monthly_payment = models.DecimalField(max_digits=15, decimal_places=2)
    application_date = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('Applied', 'Applied'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Disbursed', 'Disbursed'),
        ('Closed', 'Closed'),
    ], default='Applied')
    collateral_details = models.TextField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Loan {self.loan_reference} - User {self.user_id}"
