# loan_service/loan/models.py (lanjutan)
# loan_service/loan/models.py
from django.db import models
from django.core.cache import cache
from decimal import Decimal
import uuid
import datetime

class Loan(models.Model):
    class LoanStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PENDING = 'PENDING', 'Pending Approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        DISBURSED = 'DISBURSED', 'Disbursed'
        COMPLETED = 'COMPLETED', 'Completed'
        DEFAULTED = 'DEFAULTED', 'Defaulted'

    class LoanType(models.TextChoices):
        PERSONAL = 'PERSONAL', 'Personal Loan'
        HOME = 'HOME', 'Home Loan'
        BUSINESS = 'BUSINESS', 'Business Loan'

    loan_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user_id = models.IntegerField()
    account_id = models.IntegerField()
    loan_type = models.CharField(max_length=50, choices=LoanType.choices)
    
    # Loan details
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term_months = models.IntegerField()
    monthly_payment = models.DecimalField(max_digits=15, decimal_places=2)
    total_interest = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Additional details
    purpose = models.CharField(max_length=100)
    collateral_type = models.CharField(max_length=50, null=True)
    collateral_value = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=LoanStatus.choices,
        default=LoanStatus.DRAFT
    )
    rejection_reason = models.TextField(null=True)
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    
    # Dates
    disbursement_date = models.DateField(null=True)
    first_payment_date = models.DateField(null=True)
    maturity_date = models.DateField(null=True)
    
    # Security and tracking
    created_by = models.IntegerField()  # User ID who initiated
    approved_by = models.IntegerField(null=True)
    session_id = models.CharField(max_length=255)
    auth_token_jti = models.CharField(max_length=255)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'loans'
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['account_id']),
            models.Index(fields=['status']),
            models.Index(fields=['disbursement_date']),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Cache loan status and details
        self._update_loan_cache()

    def _update_loan_cache(self):
        """Update loan information in Redis cache"""
        cache_key = f'loan:{self.loan_id}'
        loan_data = {
            'status': self.status,
            'amount': str(self.amount),
            'monthly_payment': str(self.monthly_payment),
            'next_payment_date': self.get_next_payment_date(),
            'remaining_balance': str(self.get_remaining_balance())
        }
        cache.set(cache_key, loan_data, timeout=3600)

class LoanPayment(models.Model):
    class PaymentStatus(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        LATE = 'LATE', 'Late'

    payment_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE)
    payment_number = models.IntegerField()
    
    # Payment breakdown
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    principal_amount = models.DecimalField(max_digits=15, decimal_places=2)
    interest_amount = models.DecimalField(max_digits=15, decimal_places=2)
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Dates and status
    due_date = models.DateField()
    paid_date = models.DateField(null=True)
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.SCHEDULED
    )
    
    payment_method = models.CharField(max_length=50)
    transaction_reference = models.CharField(max_length=100, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'loan_payments'
        indexes = [
            models.Index(fields=['loan', 'payment_number']),
            models.Index(fields=['due_date']),
            models.Index(fields=['status']),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update payment status in cache
        self._update_payment_cache()

    def _update_payment_cache(self):
        """Cache payment status and next payment info"""
        # Update payment status
        payment_key = f'loan_payment:{self.payment_id}'
        payment_data = {
            'status': self.status,
            'amount': str(self.amount),
            'due_date': self.due_date.isoformat(),
            'is_late': self.due_date < datetime.now().date() and self.status != self.PaymentStatus.COMPLETED
        }
        cache.set(payment_key, payment_data, timeout=3600)
        
        # Update next payment info for loan
        if self.status == self.PaymentStatus.COMPLETED:
            next_payment = LoanPayment.objects.filter(
                loan=self.loan,
                status=self.PaymentStatus.SCHEDULED,
                due_date__gt=datetime.now().date()
            ).order_by('due_date').first()
            
            if next_payment:
                loan_key = f'loan:{self.loan.loan_id}:next_payment'
                cache.set(loan_key, {
                    'payment_id': str(next_payment.payment_id),
                    'due_date': next_payment.due_date.isoformat(),
                    'amount': str(next_payment.amount)
                }, timeout=86400)  # Cache for 24 hours

class LoanDocument(models.Model):
    class DocumentType(models.TextChoices):
        APPLICATION = 'APPLICATION', 'Loan Application'
        IDENTITY = 'IDENTITY', 'Identity Document'
        INCOME = 'INCOME', 'Income Proof'
        COLLATERAL = 'COLLATERAL', 'Collateral Document'
        CONTRACT = 'CONTRACT', 'Loan Contract'
        PAYMENT = 'PAYMENT', 'Payment Proof'

    class VerificationStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending Verification'
        VERIFIED = 'VERIFIED', 'Verified'
        REJECTED = 'REJECTED', 'Rejected'
        EXPIRED = 'EXPIRED', 'Expired'

    document_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE)
    document_type = models.CharField(max_length=50, choices=DocumentType.choices)
    document_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)
    file_size = models.IntegerField()  # in bytes
    
    # Verification
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING
    )
    verified_by = models.IntegerField(null=True)
    verification_notes = models.TextField(null=True)
    verified_at = models.DateTimeField(null=True)
    
    # Metadata
    metadata = models.JSONField(default=dict)
    is_archived = models.BooleanField(default=False)
    uploaded_by = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'loan_documents'
        indexes = [
            models.Index(fields=['loan', 'document_type']),
            models.Index(fields=['verification_status']),
            models.Index(fields=['uploaded_at']),
        ]

class LoanSchedule(models.Model):
    """Stores the complete amortization schedule for a loan"""
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE)
    payment_number = models.IntegerField()
    payment_date = models.DateField()
    payment_amount = models.DecimalField(max_digits=15, decimal_places=2)
    principal_amount = models.DecimalField(max_digits=15, decimal_places=2)
    interest_amount = models.DecimalField(max_digits=15, decimal_places=2)
    remaining_balance = models.DecimalField(max_digits=15, decimal_places=2)
    
    class Meta:
        db_table = 'loan_schedules'
        unique_together = ('loan', 'payment_number')
        indexes = [
            models.Index(fields=['loan', 'payment_date']),
        ]

class LoanStatusHistory(models.Model):
    """Tracks all status changes for audit purposes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE)
    from_status = models.CharField(max_length=20, choices=Loan.LoanStatus.choices)
    to_status = models.CharField(max_length=20, choices=Loan.LoanStatus.choices)
    changed_by = models.IntegerField()
    change_reason = models.TextField()
    
    # Security tracking
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255)
    session_id = models.CharField(max_length=255)
    auth_token_jti = models.CharField(max_length=255)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'loan_status_history'
        indexes = [
            models.Index(fields=['loan', 'created_at']),
        ]

class LoanCalculationService:
    """Helper class for loan calculations with Redis caching"""
    
    @staticmethod
    def calculate_monthly_payment(principal: Decimal, interest_rate: Decimal, term_months: int) -> Decimal:
        cache_key = f'loan_calc:{principal}:{interest_rate}:{term_months}'
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return Decimal(cached_result)
            
        # Calculate monthly payment using amortization formula
        monthly_rate = interest_rate / Decimal('100') / Decimal('12')
        payment = principal * (
            monthly_rate * (1 + monthly_rate) ** term_months
        ) / ((1 + monthly_rate) ** term_months - 1)
        
        # Cache result for 24 hours
        cache.set(cache_key, str(payment), timeout=86400)
        
        return payment

    @staticmethod
    def generate_amortization_schedule(loan: Loan) -> List[Dict]:
        cache_key = f'loan_schedule:{loan.loan_id}'
        cached_schedule = cache.get(cache_key)
        
        if cached_schedule:
            return cached_schedule
            
        schedule = []
        remaining_balance = loan.amount
        monthly_rate = loan.interest_rate / Decimal('100') / Decimal('12')
        
        for month in range(1, loan.term_months + 1):
            interest_payment = remaining_balance * monthly_rate
            principal_payment = loan.monthly_payment - interest_payment
            remaining_balance -= principal_payment
            
            schedule.append({
                'payment_number': month,
                'payment_date': loan.first_payment_date + relativedelta(months=month-1),
                'payment_amount': loan.monthly_payment,
                'principal_amount': principal_payment,
                'interest_amount': interest_payment,
                'remaining_balance': remaining_balance
            })
        
        # Cache schedule for 1 hour
        cache.set(cache_key, schedule, timeout=3600)
        
        return schedule
