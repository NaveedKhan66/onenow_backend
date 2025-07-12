"""
Reusable validators for input validation.
"""

from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, date
import re


def validate_phone_number(phone_number):
    """
    Validate phone number format.
    """
    pattern = r'^[\+]?[1-9][\d]{0,15}$'
    if not re.match(pattern, phone_number):
        raise ValidationError(
            'Invalid phone number format. Use international format without spaces.'
        )


def validate_license_plate(plate_number):
    """
    Validate license plate format.
    """
    if not plate_number or len(plate_number) < 3 or len(plate_number) > 10:
        raise ValidationError(
            'License plate must be between 3 and 10 characters long.'
        )
    
    # Allow alphanumeric characters and hyphens
    pattern = r'^[A-Z0-9\-]+$'
    if not re.match(pattern, plate_number.upper()):
        raise ValidationError(
            'License plate can only contain letters, numbers, and hyphens.'
        )


def validate_year(year):
    """
    Validate vehicle year.
    """
    current_year = timezone.now().year
    if year < 1900 or year > current_year + 1:
        raise ValidationError(
            f'Year must be between 1900 and {current_year + 1}.'
        )


def validate_booking_dates(start_date, end_date):
    """
    Validate booking start and end dates.
    """
    if not isinstance(start_date, (date, datetime)):
        raise ValidationError('Start date must be a valid date.')
    
    if not isinstance(end_date, (date, datetime)):
        raise ValidationError('End date must be a valid date.')
    
    # Convert to dates if datetime objects
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime):
        end_date = end_date.date()
    
    today = timezone.now().date()
    
    if start_date < today:
        raise ValidationError('Start date cannot be in the past.')
    
    if end_date < start_date:
        raise ValidationError('End date must be after or equal to start date.')
    
    # Limit booking duration to 365 days
    if (end_date - start_date).days > 365:
        raise ValidationError('Booking duration cannot exceed 365 days.')


def validate_positive_decimal(value):
    """
    Validate that a decimal value is positive.
    """
    if value <= 0:
        raise ValidationError('Value must be positive.')


def validate_deposit_amount(amount):
    """
    Validate deposit amount.
    """
    if amount < 0:
        raise ValidationError('Deposit amount cannot be negative.')
    
    if amount > 50000:  # Maximum deposit of $50,000
        raise ValidationError('Deposit amount cannot exceed $50,000.')


class VehicleValidator:
    """
    Validator for vehicle-related data.
    """
    
    @staticmethod
    def validate_vehicle_data(make, model, year, plate_number):
        """
        Validate all vehicle data at once.
        """
        errors = {}
        
        # Validate make
        if not make or len(make.strip()) < 2:
            errors['make'] = 'Make must be at least 2 characters long.'
        
        # Validate model
        if not model or len(model.strip()) < 2:
            errors['model'] = 'Model must be at least 2 characters long.'
        
        # Validate year
        try:
            validate_year(year)
        except ValidationError as e:
            errors['year'] = str(e)
        
        # Validate plate number
        try:
            validate_license_plate(plate_number)
        except ValidationError as e:
            errors['plate_number'] = str(e)
        
        if errors:
            raise ValidationError(errors)
        
        return True


class BookingValidator:
    """
    Validator for booking-related data.
    """
    
    @staticmethod
    def validate_booking_data(start_date, end_date, vehicle=None):
        """
        Validate all booking data at once.
        """
        errors = {}
        
        # Validate dates
        try:
            validate_booking_dates(start_date, end_date)
        except ValidationError as e:
            errors['dates'] = str(e)
        
        if errors:
            raise ValidationError(errors)
        
        return True 