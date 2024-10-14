from django.db import models
import uuid

class Payment(models.Model):
    BILL_TYPE_CHOICES = [
        ('ELECTRICITY', 'Electricity'),
        ('WATER', 'Water'),
        ('TELEPHONE', 'Telephone'),
        ('INTERNET', 'Internet'),
        ('OTHER', 'Other'),
    ]

    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    id = models.AutoField(primary_key=True)
    payment_reference = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    account_id = models.IntegerField()  # ID dari Account Service
    payee = models.CharField(max_length=255)
    bill_type = models.CharField(max_length=20, choices=BILL_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3)
    due_date = models.DateField()
    payment_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='SCHEDULED')
    recurring = models.BooleanField(default=False)
    frequency = models.CharField(max_length=10, null=True, blank=True)  # e.g., Monthly, Weekly
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return str(self.payment_reference)
