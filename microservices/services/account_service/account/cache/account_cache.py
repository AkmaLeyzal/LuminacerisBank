# account/cache/account_cache.py

from django.core.cache import cache
from django.conf import settings
from typing import Dict, Any, Optional, List
from decimal import Decimal
import json
import logging

logger = logging.getLogger(__name__)

class AccountCache:
    """Handle caching for account-related data"""

    @staticmethod
    def _get_account_details_key(account_id: str) -> str:
        """Generate cache key for account details"""
        return settings.CACHE_KEYS['ACCOUNT_DETAILS'].format(account_id)

    @staticmethod
    def _get_balance_key(account_id: str) -> str:
        """Generate cache key for balance"""
        return settings.CACHE_KEYS['BALANCE'].format(account_id)

    @staticmethod
    def _get_daily_limit_key(account_id: str) -> str:
        """Generate cache key for daily limit"""
        return settings.CACHE_KEYS['DAILY_LIMIT'].format(account_id)

    @staticmethod
    def _get_transaction_history_key(account_id: str) -> str:
        """Generate cache key for transaction history"""
        return settings.CACHE_KEYS['TRANSACTION_HISTORY'].format(account_id)

    def get_account_details(self, account_id: str) -> Optional[Dict]:
        """Get account details from cache"""
        try:
            key = self._get_account_details_key(account_id)
            data = cache.get(key)
            if data:
                logger.debug(f"Cache hit for account details: {account_id}")
                return data
            logger.debug(f"Cache miss for account details: {account_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting account details from cache: {str(e)}")
            return None

    def set_account_details(self, account_id: str, details: Dict) -> bool:
        """Set account details in cache"""
        try:
            key = self._get_account_details_key(account_id)
            cache.set(
                key, 
                details, 
                timeout=settings.CACHE_TTL['ACCOUNT_DETAILS']
            )
            logger.debug(f"Cached account details: {account_id}")
            return True
        except Exception as e:
            logger.error(f"Error caching account details: {str(e)}")
            return False

    def get_balance(self, account_id: str) -> Optional[Decimal]:
        """Get account balance from cache"""
        try:
            key = self._get_balance_key(account_id)
            data = cache.get(key)
            if data:
                logger.debug(f"Cache hit for balance: {account_id}")
                return Decimal(str(data))
            logger.debug(f"Cache miss for balance: {account_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting balance from cache: {str(e)}")
            return None

    def set_balance(self, account_id: str, balance: Decimal) -> bool:
        """Set account balance in cache"""
        try:
            key = self._get_balance_key(account_id)
            cache.set(
                key, 
                str(balance), 
                timeout=settings.CACHE_TTL['BALANCE']
            )
            logger.debug(f"Cached balance for account: {account_id}")
            return True
        except Exception as e:
            logger.error(f"Error caching balance: {str(e)}")
            return False

    def get_daily_limit_usage(self, account_id: str) -> Decimal:
        """Get daily transfer limit usage from cache"""
        try:
            key = self._get_daily_limit_key(account_id)
            data = cache.get(key)
            if data is not None:
                logger.debug(f"Cache hit for daily limit: {account_id}")
                return Decimal(str(data))
            logger.debug(f"Cache miss for daily limit: {account_id}")
            return Decimal('0')
        except Exception as e:
            logger.error(f"Error getting daily limit from cache: {str(e)}")
            return Decimal('0')

    def increment_daily_limit_usage(self, account_id: str, amount: Decimal) -> bool:
        """Increment daily transfer limit usage"""
        try:
            key = self._get_daily_limit_key(account_id)
            current = self.get_daily_limit_usage(account_id)
            new_value = current + amount
            
            # Set with TTL until end of day
            import datetime
            now = datetime.datetime.now()
            seconds_until_midnight = ((24 - now.hour - 1) * 3600) + \
                                   ((60 - now.minute - 1) * 60) + \
                                   (60 - now.second)
            
            cache.set(key, str(new_value), timeout=seconds_until_midnight)
            logger.debug(f"Updated daily limit usage for account: {account_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating daily limit usage: {str(e)}")
            return False

    def get_transaction_history(self, account_id: str, page: int, 
                              page_size: int) -> Optional[Dict]:
        """Get transaction history from cache"""
        try:
            key = self._get_transaction_history_key(account_id)
            data = cache.get(key)
            if data:
                # Handle pagination in memory
                start = (page - 1) * page_size
                end = start + page_size
                paginated_data = {
                    'results': data['transactions'][start:end],
                    'total': len(data['transactions']),
                    'page': page,
                    'page_size': page_size
                }
                logger.debug(f"Cache hit for transaction history: {account_id}")
                return paginated_data
            logger.debug(f"Cache miss for transaction history: {account_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting transaction history from cache: {str(e)}")
            return None

    def set_transaction_history(self, account_id: str, 
                              transactions: List[Dict]) -> bool:
        """Set transaction history in cache"""
        try:
            key = self._get_transaction_history_key(account_id)
            cache.set(
                key,
                {'transactions': transactions},
                timeout=settings.CACHE_TTL['TRANSACTION_HISTORY']
            )
            logger.debug(f"Cached transaction history for account: {account_id}")
            return True
        except Exception as e:
            logger.error(f"Error caching transaction history: {str(e)}")
            return False

    def invalidate_account_cache(self, account_id: str) -> None:
        """Invalidate all cache entries for an account"""
        try:
            cache.delete_many([
                self._get_account_details_key(account_id),
                self._get_balance_key(account_id),
                self._get_transaction_history_key(account_id)
            ])
            logger.info(f"Invalidated all cache for account: {account_id}")
        except Exception as e:
            logger.error(f"Error invalidating account cache: {str(e)}")