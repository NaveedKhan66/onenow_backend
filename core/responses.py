"""
Unified response structures for consistent API responses.
"""

from rest_framework.response import Response
from rest_framework import status


class StandardResponse:
    """
    Standardized response format for all API endpoints.
    """
    
    @staticmethod
    def success(data=None, message="Success", status_code=status.HTTP_200_OK):
        """
        Success response format.
        """
        response_data = {
            'success': True,
            'message': message,
            'data': data
        }
        return Response(response_data, status=status_code)
    
    @staticmethod
    def error(message="Error occurred", errors=None, error_code=None, status_code=status.HTTP_400_BAD_REQUEST):
        """
        Error response format.
        """
        response_data = {
            'success': False,
            'message': message,
            'errors': errors or {},
        }
        
        if error_code:
            response_data['error_code'] = error_code
            
        return Response(response_data, status=status_code)
    
    @staticmethod
    def created(data=None, message="Resource created successfully"):
        """
        Success response for resource creation.
        """
        return StandardResponse.success(data, message, status.HTTP_201_CREATED)
    
    @staticmethod
    def no_content(message="Operation completed successfully"):
        """
        Success response for operations that don't return data.
        """
        return StandardResponse.success(None, message, status.HTTP_204_NO_CONTENT) 