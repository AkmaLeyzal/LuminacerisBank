# accounts/services.py

from django.db import transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Dict, Any, Optional
from decimal import Decimal
import logging
import uuid

from .models import BankAccount, AccountBalanceLog
from .cache.account_cache import AccountCache
from kafka_cloud.producer import KafkaProducer
from kafka_cloud.topics import KafkaTopics

logger = logging.getLogger(__name__)

class AccountService:
    """Service for managing bank accounts"""
    
    def __init__(self):
        self.kafka_producer = KafkaProducer()
        self.cache = AccountCache()

    def get_account_details(self, account_id: str) -> Dict[str, Any]:
        """Get account details with caching"""
        cached_details = self.cache.get_account_details(account_id)
        if cached_details:
            return cached_details

        account = BankAccount.objects.get(id=account_id)
        account_data = {
            'id': str(account.id),
            'account_number': account.account_number,
            'balance': str(account.balance),
            'available_balance': str(account.available_balance),
            'hold_amount': str(account.hold_amount),
            'status': account.status,
            'last_activity': account.last_activity.isoformat()
        }

        self.cache.set_account_details(account_id, account_data)
        return account_data

    @transaction.atomic
    def create_account(self, user_id: int, account_type: str,
                      currency: str, initial_deposit: Decimal) -> BankAccount:
        """Create new bank account"""
        try:
            account = BankAccount.objects.create(
                user_id=user_id,
                account_number=self._generate_account_number(),
                account_type=account_type,
                currency=currency,
                balance=initial_deposit,
                available_balance=initial_deposit,
                status=BankAccount.AccountStatus.ACTIVE
            )

            # Create initial balance log
            AccountBalanceLog.objects.create(
                account=account,
                old_balance=Decimal('0'),
                new_balance=initial_deposit,
                change_amount=initial_deposit,
                change_type='CREDIT',
                description="Initial deposit"
            )

            # Notify other services
            self._publish_account_created_event(account)

            return account

        except Exception as e:
            logger.error(f"Error creating account: {str(e)}")
            raise ValidationError("Failed to create account")

    @transaction.atomic
    def update_account_status(self, account_id: str, 
                            status: str, reason: str = None) -> Dict[str, Any]:
        """Update account status"""
        try:
            account = BankAccount.objects.select_for_update().get(id=account_id)
            old_status = account.status
            account.status = status
            account.save()

            # Notify status change
            self._publish_account_status_changed_event(
                account, old_status, status, reason
            )

            # Invalidate cache
            self.cache.invalidate_account_cache(account_id)

            return {
                'status': 'success',
                'account_id': account_id,
                'new_status': status
            }

        except Exception as e:
            logger.error(f"Error updating account status: {str(e)}")
            raise ValidationError("Failed to update account status")

    @transaction.atomic
    def place_hold_amount(self, account_id: str, amount: Decimal,
                         reason: str, reference: str) -> Dict[str, Any]:
        """Place hold on account balance"""
        try:
            account = BankAccount.objects.select_for_update().get(id=account_id)
            
            if account.available_balance < amount:
                raise ValidationError("Insufficient available balance")

            account.hold_amount += amount
            account.available_balance -= amount
            account.save()

            # Invalidate cache
            self.cache.invalidate_account_cache(account_id)

            return {
                'status': 'success',
                'hold_reference': reference,
                'amount': str(amount),
                'available_balance': str(account.available_balance)
            }

        except Exception as e:
            logger.error(f"Error placing hold amount: {str(e)}")
            raise ValidationError("Failed to place hold amount")

    def _generate_account_number(self) -> str:
        """Generate unique account number"""
        while True:
            account_number = f"1{uuid.uuid4().hex[:9]}"
            if not BankAccount.objects.filter(account_number=account_number).exists():
                return account_number

    def _publish_account_created_event(self, account: BankAccount) -> None:
        """Publish account creation event to Kafka"""
        try:
            self.kafka_producer.produce(
                topic=KafkaTopics.ACCOUNT_EVENTS,
                key=str(account.id),
                value={
                    'event_type': 'ACCOUNT_CREATED',
                    'account_id': str(account.id),
                    'user_id': account.user_id,
                    'account_number': account.account_number,
                    'account_type': account.account_type,
                    'currency': account.currency,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error publishing account created event: {str(e)}")

    def _publish_account_status_changed_event(
        self, account: BankAccount, old_status: str,
        new_status: str, reason: str = None
    ) -> None:
        """Publish account status change event to Kafka"""
        try:
            self.kafka_producer.produce(
                topic=KafkaTopics.ACCOUNT_EVENTS,
                key=str(account.id),
                value={
                    'event_type': 'ACCOUNT_STATUS_CHANGED',
                    'account_id': str(account.id),
                    'old_status': old_status,
                    'new_status': new_status,
                    'reason': reason,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error publishing status change event: {str(e)}")