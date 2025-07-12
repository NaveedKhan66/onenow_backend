"""
Booking serializers for data validation and serialization.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from vehicles.models import Vehicle
from vehicles.serializers import VehicleListSerializer
from .models import Booking, BookingPayment, BookingCancellation
from core.validators import BookingValidator

User = get_user_model()


class BookingCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new bookings.
    """
    class Meta:
        model = Booking
        fields = [
            'vehicle', 'start_date', 'end_date', 'start_time', 'end_time',
            'customer_name', 'customer_email', 'customer_phone',
            'customer_address', 'driver_license_number', 'pickup_location',
            'return_location', 'pickup_notes', 'return_notes',
            'special_requests', 'terms_accepted'
        ]
        extra_kwargs = {
            'vehicle': {'required': True},
            'start_date': {'required': True},
            'end_date': {'required': True},
            'customer_name': {'required': True},
            'customer_email': {'required': True},
            'customer_phone': {'required': True},
            'customer_address': {'required': True},
            'driver_license_number': {'required': True},
            'pickup_location': {'required': True},
            'return_location': {'required': True},
            'terms_accepted': {'required': True},
        }
    
    def validate(self, attrs):
        """
        Validate booking data.
        """
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        vehicle = attrs.get('vehicle')
        
        # Use custom validator
        BookingValidator.validate_booking_data(start_date, end_date, vehicle)
        
        # Check if terms are accepted
        if not attrs.get('terms_accepted', False):
            raise serializers.ValidationError({
                'terms_accepted': 'You must accept the terms and conditions.'
            })
        
        return attrs
    
    def validate_vehicle(self, value):
        """
        Validate vehicle availability.
        """
        if not value.is_available:
            raise serializers.ValidationError('Vehicle is not available for booking.')
        
        return value
    
    def create(self, validated_data):
        """
        Create booking with the current user as customer.
        """
        validated_data['customer'] = self.context['request'].user
        
        # Get vehicle rates
        vehicle = validated_data['vehicle']
        validated_data['daily_rate'] = vehicle.daily_rate
        validated_data['deposit_amount'] = vehicle.deposit_amount
        
        # Default pickup and return locations to vehicle's location if not specified
        if not validated_data.get('pickup_location'):
            validated_data['pickup_location'] = vehicle.pickup_location
        if not validated_data.get('return_location'):
            validated_data['return_location'] = vehicle.pickup_location
        
        return super().create(validated_data)


class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for booking CRUD operations.
    """
    customer_name_display = serializers.CharField(source='customer.get_full_name', read_only=True)
    vehicle_info = VehicleListSerializer(source='vehicle', read_only=True)
    duration_days = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    can_be_cancelled = serializers.BooleanField(read_only=True)
    can_be_modified = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'booking_id', 'customer', 'customer_name_display',
            'vehicle', 'vehicle_info', 'start_date', 'end_date',
            'start_time', 'end_time', 'status', 'payment_status',
            'daily_rate', 'total_days', 'subtotal', 'deposit_amount',
            'discount_amount', 'total_amount', 'customer_name',
            'customer_email', 'customer_phone', 'customer_address',
            'driver_license_number', 'pickup_location', 'return_location',
            'pickup_notes', 'return_notes', 'special_requests',
            'terms_accepted', 'duration_days', 'is_active',
            'can_be_cancelled', 'can_be_modified', 'created_at',
            'updated_at', 'confirmed_at', 'cancelled_at'
        ]
        read_only_fields = [
            'id', 'booking_id', 'customer', 'customer_name_display',
            'vehicle_info', 'daily_rate', 'total_days', 'subtotal',
            'total_amount', 'duration_days', 'is_active', 'can_be_cancelled',
            'can_be_modified', 'created_at', 'updated_at', 'confirmed_at',
            'cancelled_at'
        ]


class BookingListSerializer(serializers.ModelSerializer):
    """
    Serializer for booking list view (minimal data).
    """
    customer_name_display = serializers.CharField(source='customer.get_full_name', read_only=True)
    vehicle_info = serializers.SerializerMethodField()
    duration_days = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'booking_id', 'customer_name_display', 'vehicle_info',
            'start_date', 'end_date', 'status', 'payment_status',
            'total_amount', 'duration_days', 'created_at'
        ]
    
    def get_vehicle_info(self, obj):
        """Get basic vehicle information."""
        return {
            'id': obj.vehicle.id,
            'display_name': obj.vehicle.display_name,
            'plate_number': obj.vehicle.plate_number,
            'make': obj.vehicle.make,
            'model': obj.vehicle.model,
            'year': obj.vehicle.year,
        }


class BookingPaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for booking payments.
    """
    class Meta:
        model = BookingPayment
        fields = [
            'id', 'booking', 'payment_method', 'payment_type',
            'amount', 'currency', 'transaction_id', 'is_successful',
            'processed_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'transaction_id', 'is_successful', 'processed_at',
            'created_at'
        ]


class BookingCancellationSerializer(serializers.ModelSerializer):
    """
    Serializer for booking cancellations.
    """
    cancelled_by_name = serializers.CharField(source='cancelled_by.get_full_name', read_only=True)
    
    class Meta:
        model = BookingCancellation
        fields = [
            'id', 'booking', 'reason', 'cancelled_by', 'cancelled_by_name',
            'refund_amount', 'cancellation_fee', 'created_at'
        ]
        read_only_fields = [
            'id', 'booking', 'cancelled_by', 'cancelled_by_name',
            'created_at'
        ]


class BookingAvailabilitySerializer(serializers.Serializer):
    """
    Serializer for checking booking availability.
    """
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    
    def validate(self, attrs):
        """
        Validate date range.
        """
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        # Use custom validator
        BookingValidator.validate_booking_data(start_date, end_date)
        
        return attrs


class BookingUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating bookings.
    """
    class Meta:
        model = Booking
        fields = [
            'start_date', 'end_date', 'start_time', 'end_time',
            'customer_name', 'customer_email', 'customer_phone',
            'customer_address', 'driver_license_number', 'pickup_location',
            'return_location', 'pickup_notes', 'return_notes',
            'special_requests'
        ]
    
    def validate(self, attrs):
        """
        Validate booking update data.
        """
        instance = self.instance
        
        # Check if booking can be modified
        if not instance.can_be_modified:
            raise serializers.ValidationError('Booking cannot be modified at this time.')
        
        start_date = attrs.get('start_date', instance.start_date)
        end_date = attrs.get('end_date', instance.end_date)
        
        # Use custom validator
        BookingValidator.validate_booking_data(start_date, end_date)
        
        return attrs


class StripePaymentSerializer(serializers.Serializer):
    """
    Serializer for Stripe payment processing.
    """
    payment_method_id = serializers.CharField(
        max_length=100,
        help_text="Stripe payment method ID"
    )
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Payment amount"
    )
    currency = serializers.CharField(
        max_length=3,
        default='PKR',
        help_text="Payment currency"
    )
    
    def validate_amount(self, value):
        """
        Validate payment amount.
        """
        if value <= 0:
            raise serializers.ValidationError('Payment amount must be positive.')
        
        if value > 1000000:  # Maximum payment amount
            raise serializers.ValidationError('Payment amount cannot exceed 1,000,000.')
        
        return value 