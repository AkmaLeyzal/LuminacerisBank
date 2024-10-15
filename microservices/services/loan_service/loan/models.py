from django.db import models
import uuid

class LoanApplication(models.Model):
    LOAN_TYPE_CHOICES = [
        ('PERSONAL', 'Personal'),
        ('MORTGAGE', 'Mortgage'),
        ('VEHICLE', 'Vehicle'),
    ]

    STATUS_CHOICES = [
        ('APPLIED', 'Applied'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('PAID', 'Paid'),
    ]

    id = models.AutoField(primary_key=True)
    loan_reference = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user_id = models.IntegerField()  # ID dari Auth Service
    loan_type = models.CharField(max_length=10, choices=LOAN_TYPE_CHOICES)
    principal_amount = models.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term_months = models.IntegerField()
    monthly_payment = models.DecimalField(max_digits=15, decimal_places=2)
    application_date = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='APPLIED')
    collateral_details = models.TextField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_monthly_payment(self):
        # Implementasi sederhana untuk menghitung pembayaran bulanan
        # Formula: (P * r * (1 + r)^n) / ((1 + r)^n - 1)
        P = self.principal_amount
        r = self.interest_rate / 100 / 12  # Bunga bulanan
        n = self.term_months
        if r == 0:
            return P / n
        payment = (P * r * (1 + r) ** n) / ((1 + r) ** n - 1)
        return round(payment, 2)
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.monthly_payment = self.calculate_monthly_payment()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return str(self.loan_reference)
