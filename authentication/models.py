"""
Authentication models for user management.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from core.validators import validate_phone_number


class User(AbstractUser):
    """
    Custom user model with additional fields for car rental business.
    """
    email = models.EmailField(unique=True, blank=False)
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        validators=[validate_phone_number],
        help_text="Phone number in international format"
    )
    date_of_birth = models.DateField(null=True, blank=True)
    driver_license_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Driver's license number"
    )
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    
    # Override username to use email as primary identifier
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        
    def __str__(self):
        return f"{self.email} - {self.get_full_name()}"
    
    def get_full_name(self):
        """Return the full name of the user."""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def is_profile_complete(self):
        """Check if user profile is complete."""
        return all([
            self.first_name,
            self.last_name,
            self.phone_number,
            self.date_of_birth,
            self.driver_license_number,
            self.address,
        ])


class UserProfile(models.Model):
    """
    Extended user profile information.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, max_length=500)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[validate_phone_number]
    )
    preferred_language = models.CharField(
        max_length=10,
        choices=[
            ('en', 'English'),
            ('ur', 'Urdu'),
            ('hi', 'Hindi'),
        ],
        default='en'
    )
    
    class Meta:
        db_table = 'user_profile'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        
    def __str__(self):
        return f"Profile of {self.user.email}"
