from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid
from .utils.validators import validate_full_name, validate_phone_number, validate_tax_number

class UserProfile(models.Model):
    class Gender(models.TextChoices):
        MALE = 'MALE', 'Male'
        FEMALE = 'FEMALE', 'Female'
        OTHER = 'OTHER', 'Other'
        PREFER_NOT_TO_SAY = 'PREFER_NOT_TO_SAY', 'Prefer not to say'

    profile_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(unique=True)
    full_name = models.CharField(
        max_length=255,
        validators=[validate_full_name]
    )
    tax_number = models.CharField(
        max_length=50,
        unique=True,
        validators=[validate_tax_number]
    )
    phone_number = models.CharField(
        max_length=20,
        validators=[validate_phone_number]
    )
    birth_date = models.DateField()
    gender = models.CharField(
        max_length=20,
        choices=Gender.choices,
        default=Gender.PREFER_NOT_TO_SAY
    )
    occupation = models.CharField(max_length=100)
    monthly_income = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['tax_number']),
        ]

    def __str__(self):
        return f"{self.full_name} (ID: {self.profile_id})"

class UserDocument(models.Model):
    class DocumentType(models.TextChoices):
        PASSPORT = 'PASSPORT', 'Passport'
        IDENTITY_CARD = 'IDENTITY_CARD', 'Identity Card'
        DRIVING_LICENSE = 'DRIVING_LICENSE', 'Driving License'
        TAX_ID = 'TAX_ID', 'Tax ID Card'

    document_id = models.AutoField(primary_key=True)
    profile = models.ForeignKey(
        UserProfile,
        related_name='documents',
        on_delete=models.CASCADE
    )
    document_type = models.CharField(max_length=50, choices=DocumentType.choices)
    document_number = models.CharField(max_length=100, unique=True)
    expiry_date = models.DateField()
    verification_status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_documents'
        indexes = [
            models.Index(fields=['profile']),
            models.Index(fields=['document_number']),
            models.Index(fields=['verification_status']),
        ]