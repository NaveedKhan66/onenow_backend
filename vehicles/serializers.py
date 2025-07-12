"""
Vehicle serializers for data validation and serialization.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Vehicle, VehicleImage, VehicleReview
from core.validators import VehicleValidator

User = get_user_model()


class VehicleImageSerializer(serializers.ModelSerializer):
    """
    Serializer for vehicle images.
    """
    class Meta:
        model = VehicleImage
        fields = ['id', 'image', 'caption', 'is_primary', 'created_at']
        read_only_fields = ['id', 'created_at']


class VehicleReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for vehicle reviews.
    """
    reviewer_name = serializers.CharField(source='reviewer.get_full_name', read_only=True)
    reviewer_email = serializers.EmailField(source='reviewer.email', read_only=True)
    
    class Meta:
        model = VehicleReview
        fields = [
            'id', 'rating', 'comment', 'reviewer_name', 'reviewer_email',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class VehicleSerializer(serializers.ModelSerializer):
    """
    Serializer for vehicle CRUD operations.
    """
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    display_name = serializers.CharField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    is_insurance_valid = serializers.BooleanField(read_only=True)
    is_registration_valid = serializers.BooleanField(read_only=True)
    images = VehicleImageSerializer(many=True, read_only=True)
    reviews = VehicleReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'owner_name', 'make', 'model', 'year', 'plate_number',
            'color', 'fuel_type', 'transmission', 'body_type', 'engine_capacity',
            'seating_capacity', 'features', 'daily_rate', 'deposit_amount',
            'mileage_limit', 'status', 'is_active', 'pickup_location',
            'insurance_policy_number', 'insurance_expiry', 'registration_expiry',
            'last_service_date', 'display_name', 'is_available',
            'is_insurance_valid', 'is_registration_valid', 'images', 'reviews',
            'average_rating', 'review_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'owner_name', 'display_name', 'is_available',
            'is_insurance_valid', 'is_registration_valid', 'images', 'reviews',
            'average_rating', 'review_count', 'created_at', 'updated_at'
        ]
    
    def get_average_rating(self, obj):
        """Calculate average rating for the vehicle."""
        reviews = obj.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return 0
    
    def get_review_count(self, obj):
        """Get total number of reviews for the vehicle."""
        return obj.reviews.count()
    
    def validate(self, attrs):
        """
        Validate vehicle data using custom validators.
        """
        make = attrs.get('make')
        model = attrs.get('model')
        year = attrs.get('year')
        plate_number = attrs.get('plate_number')
        
        # Use custom validator
        if make and model and year and plate_number:
            VehicleValidator.validate_vehicle_data(make, model, year, plate_number)
        
        return attrs
    
    def validate_plate_number(self, value):
        """
        Validate plate number uniqueness.
        """
        if self.instance:
            # Update case - exclude current instance
            if Vehicle.objects.filter(plate_number=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError('Vehicle with this plate number already exists.')
        else:
            # Create case
            if Vehicle.objects.filter(plate_number=value).exists():
                raise serializers.ValidationError('Vehicle with this plate number already exists.')
        
        return value.upper()
    
    def validate_daily_rate(self, value):
        """
        Validate daily rate.
        """
        if value <= 0:
            raise serializers.ValidationError('Daily rate must be positive.')
        
        if value > 100000:  # Maximum daily rate
            raise serializers.ValidationError('Daily rate cannot exceed 100,000.')
        
        return value
    
    def validate_deposit_amount(self, value):
        """
        Validate deposit amount.
        """
        if value < 0:
            raise serializers.ValidationError('Deposit amount cannot be negative.')
        
        if value > 500000:  # Maximum deposit
            raise serializers.ValidationError('Deposit amount cannot exceed 500,000.')
        
        return value


class VehicleCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new vehicles.
    """
    class Meta:
        model = Vehicle
        fields = [
            'make', 'model', 'year', 'plate_number', 'color', 'fuel_type',
            'transmission', 'body_type', 'engine_capacity', 'seating_capacity',
            'features', 'daily_rate', 'deposit_amount', 'mileage_limit',
            'pickup_location', 'insurance_policy_number', 'insurance_expiry',
            'registration_expiry', 'last_service_date'
        ]
        extra_kwargs = {
            'make': {'required': True},
            'model': {'required': True},
            'year': {'required': True},
            'plate_number': {'required': True},
            'daily_rate': {'required': True},
            'pickup_location': {'required': True},
        }
    
    def validate(self, attrs):
        """
        Validate vehicle data using custom validators.
        """
        make = attrs.get('make')
        model = attrs.get('model')
        year = attrs.get('year')
        plate_number = attrs.get('plate_number')
        
        # Use custom validator
        VehicleValidator.validate_vehicle_data(make, model, year, plate_number)
        
        return attrs
    
    def validate_plate_number(self, value):
        """
        Validate plate number uniqueness.
        """
        if Vehicle.objects.filter(plate_number=value).exists():
            raise serializers.ValidationError('Vehicle with this plate number already exists.')
        
        return value.upper()
    
    def validate_daily_rate(self, value):
        """
        Validate daily rate.
        """
        if value <= 0:
            raise serializers.ValidationError('Daily rate must be positive.')
        
        if value > 100000:  # Maximum daily rate
            raise serializers.ValidationError('Daily rate cannot exceed 100,000.')
        
        return value
    
    def create(self, validated_data):
        """
        Create vehicle with the current user as owner.
        """
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class VehicleListSerializer(serializers.ModelSerializer):
    """
    Serializer for vehicle list view (minimal data).
    """
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    display_name = serializers.CharField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    primary_image = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'owner_name', 'make', 'model', 'year', 'plate_number',
            'color', 'fuel_type', 'transmission', 'body_type', 'seating_capacity',
            'daily_rate', 'deposit_amount', 'status', 'is_available',
            'pickup_location', 'display_name', 'primary_image', 'average_rating',
            'review_count', 'created_at'
        ]
    
    def get_primary_image(self, obj):
        """Get the primary image URL."""
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return primary_image.image.url if primary_image.image else None
        return None
    
    def get_average_rating(self, obj):
        """Calculate average rating for the vehicle."""
        reviews = obj.reviews.all()
        if reviews:
            return round(sum(review.rating for review in reviews) / len(reviews), 1)
        return 0
    
    def get_review_count(self, obj):
        """Get total number of reviews for the vehicle."""
        return obj.reviews.count()


class VehicleAvailabilitySerializer(serializers.Serializer):
    """
    Serializer for checking vehicle availability.
    """
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    
    def validate(self, attrs):
        """
        Validate date range.
        """
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date >= end_date:
            raise serializers.ValidationError('End date must be after start date.')
        
        return attrs 