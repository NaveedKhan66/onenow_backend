"""
Vehicle models for car rental management.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from core.validators import validate_license_plate, validate_year

User = get_user_model()


class Vehicle(models.Model):
    """
    Vehicle model representing cars available for rental.
    """
    FUEL_TYPES = [
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('hybrid', 'Hybrid'),
        ('electric', 'Electric'),
        ('cng', 'CNG'),
    ]
    
    TRANSMISSION_TYPES = [
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
        ('semi_automatic', 'Semi-Automatic'),
    ]
    
    BODY_TYPES = [
        ('sedan', 'Sedan'),
        ('hatchback', 'Hatchback'),
        ('suv', 'SUV'),
        ('coupe', 'Coupe'),
        ('convertible', 'Convertible'),
        ('wagon', 'Wagon'),
        ('pickup', 'Pickup'),
        ('van', 'Van'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('rented', 'Rented'),
        ('maintenance', 'Under Maintenance'),
        ('inactive', 'Inactive'),
    ]
    
    # Basic Information
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')
    make = models.CharField(max_length=50, help_text="Vehicle manufacturer")
    model = models.CharField(max_length=50, help_text="Vehicle model")
    year = models.IntegerField(validators=[validate_year], help_text="Manufacturing year")
    plate_number = models.CharField(
        max_length=10,
        unique=True,
        validators=[validate_license_plate],
        help_text="License plate number"
    )
    
    # Vehicle Details
    color = models.CharField(max_length=30, blank=True)
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPES, default='petrol')
    transmission = models.CharField(max_length=20, choices=TRANSMISSION_TYPES, default='manual')
    body_type = models.CharField(max_length=20, choices=BODY_TYPES, default='sedan')
    engine_capacity = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Engine capacity in liters"
    )
    seating_capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        default=4,
        help_text="Number of seats"
    )
    
    # Additional Features
    features = models.JSONField(
        default=list,
        blank=True,
        help_text="List of vehicle features (AC, GPS, etc.)"
    )
    
    # Rental Information
    daily_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Daily rental rate"
    )
    deposit_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Security deposit amount"
    )
    mileage_limit = models.PositiveIntegerField(
        default=100,
        help_text="Daily mileage limit in kilometers"
    )
    
    # Status and Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Insurance and Documentation
    insurance_policy_number = models.CharField(max_length=100, blank=True)
    insurance_expiry = models.DateField(null=True, blank=True)
    registration_expiry = models.DateField(null=True, blank=True)
    last_service_date = models.DateField(null=True, blank=True)
    
    # Location
    pickup_location = models.CharField(
        max_length=200,
        help_text="Default pickup location"
    )
    
    class Meta:
        db_table = 'vehicles'
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['make', 'model']),
            models.Index(fields=['plate_number']),
        ]
    
    def __str__(self):
        return f"{self.year} {self.make} {self.model} ({self.plate_number})"
    
    @property
    def is_available(self):
        """Check if vehicle is available for rental."""
        return self.status == 'available' and self.is_active
    
    @property
    def display_name(self):
        """Get display name for the vehicle."""
        return f"{self.make} {self.model} ({self.year})"
    
    @property
    def is_insurance_valid(self):
        """Check if insurance is still valid."""
        if self.insurance_expiry:
            return self.insurance_expiry > timezone.now().date()
        return False
    
    @property
    def is_registration_valid(self):
        """Check if registration is still valid."""
        if self.registration_expiry:
            return self.registration_expiry > timezone.now().date()
        return False
    
    def get_available_dates(self, start_date=None, end_date=None):
        """Get available booking dates for this vehicle."""
        from bookings.models import Booking
        
        if not start_date:
            start_date = timezone.now().date()
        
        # Get all confirmed bookings for this vehicle
        bookings = Booking.objects.filter(
            vehicle=self,
            status__in=['confirmed', 'ongoing'],
            start_date__lte=end_date if end_date else timezone.now().date() + timezone.timedelta(days=365),
            end_date__gte=start_date
        )
        
        return bookings


class VehicleImage(models.Model):
    """
    Vehicle images model for storing multiple photos of vehicles.
    """
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='vehicles/', help_text="Vehicle image")
    caption = models.CharField(max_length=100, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'vehicle_images'
        verbose_name = 'Vehicle Image'
        verbose_name_plural = 'Vehicle Images'
        ordering = ['-is_primary', '-created_at']
    
    def __str__(self):
        return f"Image for {self.vehicle.display_name}"
    
    def save(self, *args, **kwargs):
        """Ensure only one primary image per vehicle."""
        if self.is_primary:
            # Set other images of this vehicle to non-primary
            VehicleImage.objects.filter(
                vehicle=self.vehicle,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)


class VehicleReview(models.Model):
    """
    Vehicle reviews and ratings from customers.
    """
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicle_reviews')
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vehicle_reviews'
        verbose_name = 'Vehicle Review'
        verbose_name_plural = 'Vehicle Reviews'
        ordering = ['-created_at']
        unique_together = ['vehicle', 'reviewer']
    
    def __str__(self):
        return f"{self.rating}-star review for {self.vehicle.display_name}"
