# account/cache/decorators.py

from functools import wraps
from django.core.cache import cache
from typing import Callable
import logging

logger = logging.getLogger(__name__)

def cache_account_details(timeout: int = None):
    """Decorator for caching account details"""
    def decorator(view_func: Callable):
        @wraps(view_func)
        def wrapper(view_instance, request, *args, **kwargs):
            account_id = kwargs.get('pk') or kwargs.get('account_id')
            if not account_id:
                return view_func(view_instance, request, *args, **kwargs)

            cache_key = f"account:{account_id}:details"
            cached_data = cache.get(cache_key)
            
            if cached_data is not None:
                logger.debug(f"Cache hit for decorator: {cache_key}")
                return cached_data

            response = view_func(view_instance, request, *args, **kwargs)
            
            if hasattr(response, 'data'):
                cache_timeout = timeout or settings.CACHE_TTL['ACCOUNT_DETAILS']
                cache.set(cache_key, response, timeout=cache_timeout)
                logger.debug(f"Cached response for: {cache_key}")

            return response
        return wrapper
    return decorator

def invalidate_account_cache(view_func: Callable):
    """Decorator for invalidating account cache"""
    @wraps(view_func)
    def wrapper(view_instance, request, *args, **kwargs):
        response = view_func(view_instance, request, *args, **kwargs)
        
        account_id = kwargs.get('pk') or kwargs.get('account_id')
        if account_id:
            from .account_cache import AccountCache
            cache_handler = AccountCache()
            cache_handler.invalidate_account_cache(account_id)
            
        return response
    return wrapper