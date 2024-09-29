# services/payment_service/payment/models.py

from django.db import models

class Payment(models.Model):
    payment_reference = models.CharField(max_length=100, unique=True)
    account_id = models.IntegerField()
    payee = models.CharField(max_length=255)
    bill_type = models.CharField(max_length=50, choices=[
        ('Electricity', 'Electricity'),
        ('Water', 'Water'),
        ('Internet', 'Internet'),
        # Tambahkan jenis tagihan lainnya
    ])
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3)
    due_date = models.DateField()
    payment_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    ], default='Scheduled')
    recurring = models.BooleanField(default=False)
    frequency = models.CharField(max_length=20, choices=[
        ('Monthly', 'Monthly'),
        ('Weekly', 'Weekly'),
        # Tambahkan frekuensi lainnya
    ], null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
