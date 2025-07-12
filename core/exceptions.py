"""
Custom exception handlers for consistent error responses.
"""

from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent error responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        error_data = {
            'success': False,
            'message': 'An error occurred',
            'errors': {}
        }
        
        if hasattr(exc, 'detail'):
            if isinstance(exc.detail, dict):
                error_data['errors'] = exc.detail
                # Set a more specific message if available
                if 'non_field_errors' in exc.detail:
                    error_data['message'] = exc.detail['non_field_errors'][0]
                else:
                    error_data['message'] = 'Validation failed'
            elif isinstance(exc.detail, list):
                error_data['message'] = exc.detail[0]
            else:
                error_data['message'] = str(exc.detail)
        
        # Handle specific exception types
        if response.status_code == status.HTTP_404_NOT_FOUND:
            error_data['message'] = 'Resource not found'
            error_data['error_code'] = 'NOT_FOUND'
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            error_data['message'] = 'Authentication required'
            error_data['error_code'] = 'UNAUTHORIZED'
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            error_data['message'] = 'Permission denied'
            error_data['error_code'] = 'FORBIDDEN'
        elif response.status_code == status.HTTP_400_BAD_REQUEST:
            error_data['error_code'] = 'BAD_REQUEST'
        elif response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            error_data['message'] = 'Internal server error'
            error_data['error_code'] = 'INTERNAL_ERROR'
        
        response.data = error_data
    
    return response


class CustomValidationError(Exception):
    """
    Custom validation error for business logic validation.
    """
    def __init__(self, message, error_code=None):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class BookingOverlapError(CustomValidationError):
    """
    Exception raised when booking dates overlap with existing bookings.
    """
    def __init__(self, message="Vehicle is already booked for the selected dates"):
        super().__init__(message, error_code='BOOKING_OVERLAP')


class PaymentProcessingError(CustomValidationError):
    """
    Exception raised when payment processing fails.
    """
    def __init__(self, message="Payment processing failed"):
        super().__init__(message, error_code='PAYMENT_FAILED') 