# transaction/services.py
import uuid
from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
import requests
from requests.exceptions import RequestException
from kafka_cloud.producer import KafkaProducer
from kafka_cloud.topics import KafkaTopics
from .models import Transaction, TransactionDetail, TransactionLimitCache, TransactionRateLimit
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class AccountService:
    """Service for interacting with Account Service"""
    
    def __init__(self):
        self.base_url = settings.ACCOUNT_SERVICE_URL
        self.timeout = 5  # seconds

    def get_account_info(self, account_id: uuid.UUID) -> Dict:
        """Get account information from Account Service"""
        try:
            response = requests.get(
                f"{self.base_url}/api/accounts/{account_id}/",
                headers=self._get_service_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logger.error(f"Error fetching account info: {str(e)}")
            raise ValueError("Unable to fetch account information")

    def check_balance(self, account_id: uuid.UUID, amount: Decimal) -> bool:
        """Check if account has sufficient balance"""
        try:
            cache_key = f'account:{account_id}:balance'
            balance = cache.get(cache_key)
            
            if balance is None:
                account_info = self.get_account_info(account_id)
                balance = Decimal(account_info['balance'])
                cache.set(cache_key, str(balance), timeout=300)  # 5 minutes cache
            else:
                balance = Decimal(balance)
            
            return balance >= amount

        except (ValueError, KeyError) as e:
            logger.error(f"Error checking balance: {str(e)}")
            raise ValueError("Unable to verify account balance")

    def process_transfer(self, transaction: Transaction) -> bool:
        """Process transfer with Account Service"""
        try:
            response = requests.post(
                f"{self.base_url}/api/accounts/transfer/",
                json={
                    'transaction_id': str(transaction.transaction_id),
                    'sender_account_id': str(transaction.sender_account_id),
                    'receiver_account_id': str(transaction.receiver_account_id),
                    'amount': str(transaction.amount),
                    'currency': transaction.currency,
                    'fee_amount': str(transaction.fee_amount),
                    'reference_number': transaction.reference_number
                },
                headers=self._get_service_headers(),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                # Invalidate balance cache for both accounts
                cache.delete(f'account:{transaction.sender_account_id}:balance')
                cache.delete(f'account:{transaction.receiver_account_id}:balance')
                return True
                
            return False

        except RequestException as e:
            logger.error(f"Error processing transfer: {str(e)}")
            return False

    def _get_service_headers(self):
        return {
            'Service-Auth-Key': settings.SERVICE_AUTH_KEY,
            'Content-Type': 'application/json'
        }

class TransactionService:
    def __init__(self):
        self.kafka_producer = KafkaProducer()
        self.account_service = AccountService()

    def initiate_transfer(self, sender_account_id: uuid.UUID, data: Dict, request_info: Dict) -> Transaction:
        """Initiate a new transfer transaction"""
        try:
            # Check rate limiting
            if not TransactionRateLimit.check_rate_limit(sender_account_id):
                raise ValueError("Transaction rate limit exceeded")

            # Validate accounts and check balance
            sender_info = self.account_service.get_account_info(sender_account_id)
            receiver_info = self.account_service.get_account_info(data['receiver_account_id'])

            if not sender_info['is_active'] or not receiver_info['is_active']:
                raise ValueError("One or both accounts are inactive")

            # Validate currencies match or handle conversion
            if sender_info['currency'] != data['currency']:
                raise ValueError("Transaction currency must match account currency")

            # Check balance
            total_amount = data['amount'] + self._calculate_fees(data['amount'])
            if not self.account_service.check_balance(sender_account_id, total_amount):
                raise ValueError("Insufficient balance")

            # Check daily limit
            if not TransactionLimitCache.check_daily_limit(sender_account_id, data['amount']):
                raise ValueError("Daily transaction limit exceeded")

            # Create transaction
            transaction = self._create_transaction(
                sender_account_id, data, request_info, 
                sender_info, total_amount
            )

            # Process immediately if not scheduled
            if not data.get('scheduled_at'):
                self._process_transaction(transaction)

            # Update rate limit
            TransactionRateLimit.increment_counter(sender_account_id)

            return transaction

        except ValueError as e:
            logger.error(f"Error initiating transfer: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in transfer: {str(e)}")
            raise ValueError("Unable to process transfer")

    def _create_transaction(
        self, sender_account_id: uuid.UUID, data: Dict, 
        request_info: Dict, sender_info: Dict, total_amount: Decimal
    ) -> Transaction:
        """Create new transaction record"""
        try:
            fee_amount = self._calculate_fees(data['amount'])
            
            transaction = Transaction.objects.create(
                reference_number=self._generate_reference_number(),
                transaction_type=data.get('transaction_type', Transaction.TransactionType.TRANSFER),
                sender_account_id=sender_account_id,
                receiver_account_id=data['receiver_account_id'],
                amount=data['amount'],
                currency=data['currency'],
                fee_amount=fee_amount,
                fee_type='TRANSFER_FEE',
                description=data.get('description', ''),
                routing_info={
                    'sender_account_type': sender_info['account_type'],
                    'transfer_method': 'INTERNAL'
                },
                scheduled_at=data.get('scheduled_at'),
                created_by=request_info['user_id'],
                ip_address=request_info['ip_address'],
                user_agent=request_info['user_agent'],
                device_id=request_info.get('device_id'),
                session_id=request_info['session_id'],
                auth_token_jti=request_info['auth_token_jti']
            )

            # Create initial detail record
            TransactionDetail.objects.create(
                transaction=transaction,
                processing_status=TransactionDetail.ProcessingStatus.INITIATED
            )

            return transaction

        except Exception as e:
            logger.error(f"Error creating transaction: {str(e)}")
            raise

    def _process_transaction(self, transaction: Transaction) -> None:
        """Process a transaction"""
        try:
            # Update status to processing
            transaction.status = Transaction.TransactionStatus.PROCESSING
            transaction.save()

            # Create processing detail
            self._create_transaction_detail(
                transaction,
                TransactionDetail.ProcessingStatus.PROCESSING
            )

            # Perform fraud check
            fraud_check_result = self._check_fraud(transaction)
            if not fraud_check_result['is_safe']:
                self._handle_fraud_detected(transaction, fraud_check_result['reason'])
                return

            # Process transfer with Account Service
            success = self.account_service.process_transfer(transaction)
            
            if success:
                self._handle_successful_transfer(transaction)
            else:
                self._handle_failed_transfer(transaction)

        except Exception as e:
            logger.error(f"Error processing transaction: {str(e)}")
            self._handle_failed_transfer(transaction, str(e))
            raise

    def _check_fraud(self, transaction: Transaction) -> Dict:
        """Check for fraudulent activity"""
        try:
            response = requests.post(
                f"{settings.FRAUD_SERVICE_URL}/api/check/",
                json={
                    'transaction_id': str(transaction.transaction_id),
                    'sender_id': str(transaction.sender_account_id),
                    'receiver_id': str(transaction.receiver_account_id),
                    'amount': str(transaction.amount),
                    'currency': transaction.currency,
                    'ip_address': transaction.ip_address,
                    'device_id': transaction.device_id,
                    'location': transaction.location
                },
                headers=self._get_service_headers(),
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'is_safe': result['risk_level'] != 'HIGH',
                    'reason': result.get('reason')
                }

            return {'is_safe': False, 'reason': 'Fraud check service unavailable'}

        except Exception as e:
            logger.error(f"Error in fraud check: {str(e)}")
            return {'is_safe': False, 'reason': 'Fraud check failed'}

    def _handle_successful_transfer(self, transaction: Transaction) -> None:
        """Handle successful transfer completion"""
        transaction.status = Transaction.TransactionStatus.COMPLETED
        transaction.executed_at = timezone.now()
        transaction.save()

        self._create_transaction_detail(
            transaction,
            TransactionDetail.ProcessingStatus.COMPLETED
        )

        # Update daily total
        TransactionLimitCache.update_daily_total(
            transaction.sender_account_id,
            transaction.amount
        )

        # Publish success event
        self._publish_transaction_event('TRANSACTION_COMPLETED', transaction)

    def _handle_failed_transfer(
        self, transaction: Transaction, 
        error_message: Optional[str] = None
    ) -> None:
        """Handle failed transfer"""
        transaction.status = Transaction.TransactionStatus.FAILED
        transaction.save()

        self._create_transaction_detail(
            transaction,
            TransactionDetail.ProcessingStatus.FAILED,
            error_message=error_message or "Transfer processing failed"
        )

        # Publish failure event
        self._publish_transaction_event('TRANSACTION_FAILED', transaction)

    def _handle_fraud_detected(
        self, transaction: Transaction, 
        reason: str
    ) -> None:
        """Handle fraud detection"""
        transaction.status = Transaction.TransactionStatus.BLOCKED
        transaction.save()

        self._create_transaction_detail(
            transaction,
            TransactionDetail.ProcessingStatus.FAILED,
            error_message=f"Fraud detected: {reason}"
        )

        # Publish fraud event
        self._publish_transaction_event('TRANSACTION_BLOCKED', transaction)

    def _calculate_fees(self, amount: Decimal) -> Decimal:
        """Calculate transaction fees"""
        base_fee = Decimal('1.00')
        percentage_fee = amount * Decimal('0.001')  # 0.1%
        return base_fee + percentage_fee

    def _generate_reference_number(self) -> str:
        """Generate unique reference number"""
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_str = str(uuid.uuid4().hex)[:6].upper()
        return f"TRX{timestamp}{random_str}"

    def _create_transaction_detail(
        self, transaction: Transaction,
        status: str, error_message: Optional[str] = None
    ) -> TransactionDetail:
        """Create transaction detail record"""
        return TransactionDetail.objects.create(
            transaction=transaction,
            processing_status=status,
            error_message=error_message
        )

    def _publish_transaction_event(
        self, event_type: str,
        transaction: Transaction
    ) -> None:
        """Publish transaction event to Kafka"""
        try:
            self.kafka_producer.produce(
                topic=KafkaTopics.TRANSACTION_EVENTS,
                key=str(transaction.transaction_id),
                value={
                    'event_type': event_type,
                    'transaction_id': str(transaction.transaction_id),
                    'reference_number': transaction.reference_number,
                    'status': transaction.status,
                    'amount': str(transaction.amount),
                    'currency': transaction.currency,
                    'sender_id': str(transaction.sender_account_id),
                    'receiver_id': str(transaction.receiver_account_id),
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error publishing event: {str(e)}")

    def get_transaction_status(self, transaction_id: uuid.UUID) -> Dict:
        """Get detailed transaction status"""
        try:
            transaction = Transaction.objects.select_related('details').get(
                transaction_id=transaction_id
            )
            latest_detail = transaction.details.order_by('-created_at').first()

            return {
                'transaction_id': transaction.transaction_id,
                'reference_number': transaction.reference_number,
                'status': transaction.status,
                'transaction_type': transaction.transaction_type,
                'amount': transaction.amount,
                'currency': transaction.currency,
                'fee_amount': transaction.fee_amount,
                'executed_at': transaction.executed_at,
                'error_message': latest_detail.error_message if latest_detail else None,
                'processing_status': latest_detail.processing_status if latest_detail else None
            }
        except Transaction.DoesNotExist:
            raise ValueError("Transaction not found")

    def reverse_transaction(
        self, transaction_id: uuid.UUID, 
        reason: str,
        reversal_amount: Optional[Decimal] = None
    ) -> Transaction:
        """Reverse a completed transaction"""
        try:
            original_transaction = Transaction.objects.get(
                transaction_id=transaction_id,
                status=Transaction.TransactionStatus.COMPLETED
            )

            amount_to_reverse = reversal_amount or original_transaction.amount

            # Create reversal transaction
            reversal = Transaction.objects.create(
                transaction_type=Transaction.TransactionType.REVERSAL,
                sender_account_id=original_transaction.receiver_account_id,
                receiver_account_id=original_transaction.sender_account_id,
                amount=amount_to_reverse,
                currency=original_transaction.currency,
                description=f"Reversal for {original_transaction.reference_number}: {reason}",
                original_transaction=original_transaction,
                created_by=original_transaction.created_by,
                ip_address=original_transaction.ip_address,
                user_agent=original_transaction.user_agent,
                device_id=original_transaction.device_id,
                session_id=original_transaction.session_id,
                auth_token_jti=original_transaction.auth_token_jti
            )

            # Process reversal
            self._process_transaction(reversal)

            # Update original transaction status
            original_transaction.status = Transaction.TransactionStatus.REVERSED
            original_transaction.save()

            return reversal

        except Transaction.DoesNotExist:
            raise ValueError("Original transaction not found or not eligible for reversal")
        except Exception as e:
            logger.error(f"Error processing reversal: {str(e)}")
            raise ValueError("Unable to process reversal")

    def _get_service_headers(self):
        """Get headers for service-to-service communication"""
        return {
            'Service-Auth-Key': settings.SERVICE_AUTH_KEY,
            'Content-Type': 'application/json'
        }