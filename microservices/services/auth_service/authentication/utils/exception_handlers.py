# authentication/utils/exception_handlers.py

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler untuk API responses
    """
    # Panggil exception handler default DRF terlebih dahulu
    response = exception_handler(exc, context)

    if response is None:
        # Jika tidak ada response dari handler default
        logger.error(f"Unhandled exception: {str(exc)}")
        response = Response({
            'error': 'Internal server error occurred.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Standarisasi format response error
    if response is not None and response.data:
        error_data = {}
        
        # Handle berbagai format error
        if isinstance(response.data, dict):
            if 'detail' in response.data:
                error_data['message'] = response.data['detail']
            elif 'non_field_errors' in response.data:
                error_data['message'] = response.data['non_field_errors'][0]
            else:
                error_data['errors'] = response.data
        elif isinstance(response.data, list):
            error_data['message'] = response.data[0]
        else:
            error_data['message'] = str(response.data)

        response.data = error_data

    return response