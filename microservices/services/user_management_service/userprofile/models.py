# user_management_service/user_management/models.py
from django.db import models

class UserProfile(models.Model):
    user_id = models.IntegerField(unique=True)  # Reference to Auth service User
    full_name = models.CharField(max_length=255)
    mother_maiden_name = models.CharField(max_length=100)
    birth_date = models.DateField()
    gender = models.CharField(max_length=20)
    marital_status = models.CharField(max_length=50)
    nationality = models.CharField(max_length=100)
    tax_number = models.CharField(max_length=50, unique=True)
    phone_number = models.CharField(max_length=20)
    occupation = models.CharField(max_length=100)
    monthly_income = models.DecimalField(max_digits=15, decimal_places=2)
    income_source = models.CharField(max_length=50)
    employment_status = models.CharField(max_length=50)
    employer_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['tax_number']),
        ]

class UserAddress(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    address_type = models.CharField(max_length=50)  # HOME/OFFICE
    street_address = models.CharField(max_length=255)
    rt_rw = models.CharField(max_length=20)
    village = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    country = models.CharField(max_length=100)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_addresses'
        indexes = [
            models.Index(fields=['profile', 'address_type']),
        ]

class UserDocument(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    document_type = models.CharField(max_length=50)  # KTP/PASSPORT/NPWP
    document_number = models.CharField(max_length=100, unique=True)
    issue_date = models.DateField()
    expiry_date = models.DateField()
    issuing_authority = models.CharField(max_length=100)
    document_path = models.CharField(max_length=255)
    verification_status = models.CharField(max_length=20)
    verification_notes = models.TextField(null=True)
    verified_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_documents'
        indexes = [
            models.Index(fields=['document_number']),
            models.Index(fields=['verification_status']),
        ]