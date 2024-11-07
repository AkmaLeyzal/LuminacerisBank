# authentication/utils/decorators.py
from functools import wraps
from .logging import CustomLogger
import time

def log_execution_time(func):
    """Decorator to log function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            CustomLogger.info(
                f'Function {func.__name__} executed in {execution_time:.2f} seconds',
                {'execution_time': execution_time}
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            CustomLogger.error(
                f'Function {func.__name__} failed after {execution_time:.2f} seconds',
                exc_info=True,
                extra={
                    'execution_time': execution_time,
                    'error': str(e)
                }
            )
            raise
    return wrapper

def handle_exceptions(error_map=None):
    """Decorator to handle exceptions with custom error mapping"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_map = error_map or {}
                error_class = error_map.get(type(e), AuthBaseException)
                
                CustomLogger.error(
                    f'Error in {func.__name__}: {str(e)}',
                    exc_info=True,
                    extra={'error_type': type(e).__name__}
                )
                
                raise error_class(str(e))
        return wrapper
    return decorator