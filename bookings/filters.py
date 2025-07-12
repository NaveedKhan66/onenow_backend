"""
Booking filters for advanced search and filtering.
"""

import django_filters
from django.db import models
from .models import Booking


class BookingFilter(django_filters.FilterSet):
    """
    Filter class for booking search and filtering.
    """
    # Basic filters
    booking_id = django_filters.CharFilter(lookup_expr='icontains')
    customer_name = django_filters.CharFilter(lookup_expr='icontains')
    customer_email = django_filters.CharFilter(lookup_expr='icontains')
    
    # Date filters
    start_date = django_filters.DateFilter()
    start_date__gte = django_filters.DateFilter(field_name='start_date', lookup_expr='gte')
    start_date__lte = django_filters.DateFilter(field_name='start_date', lookup_expr='lte')
    end_date = django_filters.DateFilter()
    end_date__gte = django_filters.DateFilter(field_name='end_date', lookup_expr='gte')
    end_date__lte = django_filters.DateFilter(field_name='end_date', lookup_expr='lte')
    
    # Status filters
    status = django_filters.ChoiceFilter(choices=Booking.STATUS_CHOICES)
    payment_status = django_filters.ChoiceFilter(choices=Booking.PAYMENT_STATUS_CHOICES)
    
    # Amount filters
    total_amount = django_filters.NumberFilter()
    total_amount__gte = django_filters.NumberFilter(field_name='total_amount', lookup_expr='gte')
    total_amount__lte = django_filters.NumberFilter(field_name='total_amount', lookup_expr='lte')
    
    # Vehicle filters
    vehicle = django_filters.NumberFilter(field_name='vehicle__id')
    vehicle_make = django_filters.CharFilter(field_name='vehicle__make', lookup_expr='icontains')
    vehicle_model = django_filters.CharFilter(field_name='vehicle__model', lookup_expr='icontains')
    
    # Location filters
    pickup_location = django_filters.CharFilter(lookup_expr='icontains')
    return_location = django_filters.CharFilter(lookup_expr='icontains')
    
    # Date range filters
    created_at__gte = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at__lte = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Custom filters
    is_active = django_filters.BooleanFilter(method='filter_is_active')
    upcoming = django_filters.BooleanFilter(method='filter_upcoming')
    past = django_filters.BooleanFilter(method='filter_past')
    
    class Meta:
        model = Booking
        fields = [
            'booking_id', 'customer_name', 'customer_email', 'start_date',
            'end_date', 'status', 'payment_status', 'total_amount',
            'vehicle', 'pickup_location', 'return_location'
        ]
    
    def filter_is_active(self, queryset, name, value):
        """
        Filter bookings by active status.
        """
        if value:
            return queryset.filter(status__in=['confirmed', 'ongoing'])
        return queryset
    
    def filter_upcoming(self, queryset, name, value):
        """
        Filter upcoming bookings.
        """
        if value:
            from django.utils import timezone
            return queryset.filter(
                start_date__gte=timezone.now().date(),
                status__in=['pending', 'confirmed']
            )
        return queryset
    
    def filter_past(self, queryset, name, value):
        """
        Filter past bookings.
        """
        if value:
            from django.utils import timezone
            return queryset.filter(
                end_date__lt=timezone.now().date(),
                status__in=['completed', 'cancelled']
            )
        return queryset 