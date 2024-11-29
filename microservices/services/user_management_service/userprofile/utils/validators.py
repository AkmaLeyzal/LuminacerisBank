# utils/validators.py
import re
from django.core.exceptions import ValidationError

def validate_tax_number(value):
    """Validate tax number format (adjust regex pattern as needed)"""
    pattern = r'^[A-Z]{2}\d{10}$'  # Example: ID1234567890
    if not re.match(pattern, value):
        raise ValidationError(
            'Tax number must be 2 capital letters followed by 10 digits'
        )

def validate_phone_number(value):
    """Validate phone number format"""
    pattern = r'^\+[1-9]\d{1,14}$'  # International format
    if not re.match(pattern, value):
        raise ValidationError(
            'Phone number must be in international format (e.g., +6281234567890)'
        )

def validate_full_name(value):
    """Validate full name format"""
    if len(value.split()) < 2:
        raise ValidationError('Full name must include at least first and last name')
    
    if not all(part.isalpha() or part.isspace() for part in value):
        raise ValidationError('Name can only contain letters and spaces')