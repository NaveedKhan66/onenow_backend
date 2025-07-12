"""
Booking models for reservation management.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid

User = get_user_model()


class Booking(models.Model):
    """
    Booking model representing car rental reservations.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partial'),
        ('refunded', 'Refunded'),
        ('failed', 'Failed'),
    ]
    
    # Booking Information
    booking_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text="Unique booking identifier"
    )
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    vehicle = models.ForeignKey('vehicles.Vehicle', on_delete=models.CASCADE, related_name='bookings')
    
    # Booking Dates
    start_date = models.DateField(help_text="Rental start date")
    end_date = models.DateField(help_text="Rental end date")
    start_time = models.TimeField(default='09:00', help_text="Pickup time")
    end_time = models.TimeField(default='18:00', help_text="Return time")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Pricing
    daily_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Daily rate at the time of booking"
    )
    total_days = models.PositiveIntegerField(help_text="Total rental days")
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Subtotal (daily_rate * total_days)"
    )
    deposit_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Security deposit amount"
    )
    discount_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Discount applied"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total amount to be paid"
    )
    
    # Customer Details
    customer_name = models.CharField(max_length=100, help_text="Customer full name")
    customer_email = models.EmailField(help_text="Customer email")
    customer_phone = models.CharField(max_length=20, help_text="Customer phone number")
    customer_address = models.TextField(help_text="Customer address")
    driver_license_number = models.CharField(max_length=50, help_text="Driver's license number")
    
    # Pickup and Return
    pickup_location = models.CharField(max_length=200, help_text="Pickup location")
    return_location = models.CharField(max_length=200, help_text="Return location")
    pickup_notes = models.TextField(blank=True, help_text="Special pickup instructions")
    return_notes = models.TextField(blank=True, help_text="Special return instructions")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Additional Information
    special_requests = models.TextField(blank=True, help_text="Special requests from customer")
    terms_accepted = models.BooleanField(default=False, help_text="Terms and conditions accepted")
    
    class Meta:
        db_table = 'bookings'
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['vehicle', 'status']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['booking_id']),
        ]
    
    def __str__(self):
        return f"Booking {self.booking_id} - {self.customer_name}"
    
    def save(self, *args, **kwargs):
        """
        Override save method to generate booking ID and calculate amounts.
        """
        if not self.booking_id:
            self.booking_id = self.generate_booking_id()
        
        # Calculate amounts
        self.calculate_amounts()
        
        # Validate booking
        self.clean()
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """
        Validate booking data.
        """
        # Validate dates
        if self.start_date >= self.end_date:
            raise ValidationError('End date must be after start date.')
        
        # Validate booking is not in the past
        if self.start_date < timezone.now().date():
            raise ValidationError('Booking cannot start in the past.')
        
        # Check vehicle availability
        if self.vehicle:
            overlapping_bookings = Booking.objects.filter(
                vehicle=self.vehicle,
                status__in=['confirmed', 'ongoing'],
                start_date__lte=self.end_date,
                end_date__gte=self.start_date
            )
            
            if self.pk:
                overlapping_bookings = overlapping_bookings.exclude(pk=self.pk)
            
            if overlapping_bookings.exists():
                raise ValidationError('Vehicle is already booked for the selected dates.')
    
    def generate_booking_id(self):
        """
        Generate unique booking ID.
        """
        prefix = 'BK'
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4())[:6].upper()
        return f"{prefix}{timestamp}{unique_id}"
    
    def calculate_amounts(self):
        """
        Calculate booking amounts.
        """
        if self.start_date and self.end_date and self.daily_rate:
            self.total_days = (self.end_date - self.start_date).days
            if self.total_days == 0:
                self.total_days = 1  # Minimum 1 day
            
            self.subtotal = self.daily_rate * self.total_days
            self.total_amount = self.subtotal + self.deposit_amount - self.discount_amount
    
    @property
    def duration_days(self):
        """Get booking duration in days."""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return 0
    
    @property
    def is_active(self):
        """Check if booking is currently active."""
        return self.status in ['confirmed', 'ongoing']
    
    @property
    def can_be_cancelled(self):
        """Check if booking can be cancelled."""
        if self.status in ['cancelled', 'completed', 'no_show']:
            return False
        
        # Allow cancellation up to 24 hours before start date
        if self.start_date:
            cancellation_deadline = timezone.now().date() + timezone.timedelta(days=1)
            return self.start_date > cancellation_deadline
        
        return True
    
    @property
    def can_be_modified(self):
        """Check if booking can be modified."""
        return self.status in ['pending', 'confirmed'] and self.can_be_cancelled
    
    def confirm_booking(self):
        """Confirm the booking."""
        if self.status == 'pending':
            self.status = 'confirmed'
            self.confirmed_at = timezone.now()
            self.save()
    
    def cancel_booking(self, reason=None):
        """Cancel the booking."""
        if self.can_be_cancelled:
            self.status = 'cancelled'
            self.cancelled_at = timezone.now()
            self.save()
            
            # Create booking cancellation record
            BookingCancellation.objects.create(
                booking=self,
                reason=reason or "Cancelled by customer",
                cancelled_by=self.customer
            )
    
    def start_rental(self):
        """Start the rental (pickup)."""
        if self.status == 'confirmed':
            self.status = 'ongoing'
            self.save()
            
            # Update vehicle status
            self.vehicle.status = 'rented'
            self.vehicle.save()
    
    def complete_rental(self):
        """Complete the rental (return)."""
        if self.status == 'ongoing':
            self.status = 'completed'
            self.save()
            
            # Update vehicle status
            self.vehicle.status = 'available'
            self.vehicle.save()


class BookingCancellation(models.Model):
    """
    Model to track booking cancellations.
    """
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='cancellation')
    reason = models.TextField(help_text="Reason for cancellation")
    cancelled_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='booking_cancellations')
    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Refund amount"
    )
    cancellation_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Cancellation fee"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'booking_cancellations'
        verbose_name = 'Booking Cancellation'
        verbose_name_plural = 'Booking Cancellations'
    
    def __str__(self):
        return f"Cancellation for {self.booking.booking_id}"


class BookingPayment(models.Model):
    """
    Model to track booking payments.
    """
    PAYMENT_METHODS = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('stripe', 'Stripe'),
    ]
    
    PAYMENT_TYPES = [
        ('deposit', 'Deposit'),
        ('full_payment', 'Full Payment'),
        ('partial_payment', 'Partial Payment'),
        ('refund', 'Refund'),
    ]
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='PKR')
    
    # Payment gateway details
    transaction_id = models.CharField(max_length=100, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Status
    is_successful = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'booking_payments'
        verbose_name = 'Booking Payment'
        verbose_name_plural = 'Booking Payments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment for {self.booking.booking_id} - {self.amount}"
