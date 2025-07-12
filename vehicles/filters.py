"""
Vehicle filters for advanced search and filtering.
"""

import django_filters
from django.db import models
from .models import Vehicle


class VehicleFilter(django_filters.FilterSet):
    """
    Filter class for vehicle search and filtering.
    """
    # Basic filters
    make = django_filters.CharFilter(lookup_expr='icontains')
    model = django_filters.CharFilter(lookup_expr='icontains')
    year = django_filters.NumberFilter()
    year__gte = django_filters.NumberFilter(field_name='year', lookup_expr='gte')
    year__lte = django_filters.NumberFilter(field_name='year', lookup_expr='lte')
    color = django_filters.CharFilter(lookup_expr='icontains')
    plate_number = django_filters.CharFilter(lookup_expr='icontains')
    
    # Vehicle type filters
    fuel_type = django_filters.ChoiceFilter(choices=Vehicle.FUEL_TYPES)
    transmission = django_filters.ChoiceFilter(choices=Vehicle.TRANSMISSION_TYPES)
    body_type = django_filters.ChoiceFilter(choices=Vehicle.BODY_TYPES)
    
    # Capacity filters
    seating_capacity = django_filters.NumberFilter()
    seating_capacity__gte = django_filters.NumberFilter(field_name='seating_capacity', lookup_expr='gte')
    seating_capacity__lte = django_filters.NumberFilter(field_name='seating_capacity', lookup_expr='lte')
    
    # Price filters
    daily_rate = django_filters.NumberFilter()
    daily_rate__gte = django_filters.NumberFilter(field_name='daily_rate', lookup_expr='gte')
    daily_rate__lte = django_filters.NumberFilter(field_name='daily_rate', lookup_expr='lte')
    
    # Status filters
    status = django_filters.ChoiceFilter(choices=Vehicle.STATUS_CHOICES)
    is_active = django_filters.BooleanFilter()
    is_available = django_filters.BooleanFilter(method='filter_is_available')
    
    # Location filter
    pickup_location = django_filters.CharFilter(lookup_expr='icontains')
    
    # Date range filters
    created_at__gte = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at__lte = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    
    # Feature filters
    has_features = django_filters.CharFilter(method='filter_has_features')
    
    class Meta:
        model = Vehicle
        fields = [
            'make', 'model', 'year', 'color', 'fuel_type', 'transmission',
            'body_type', 'seating_capacity', 'daily_rate', 'status',
            'is_active', 'pickup_location'
        ]
    
    def filter_is_available(self, queryset, name, value):
        """
        Filter vehicles by availability status.
        """
        if value:
            return queryset.filter(status='available', is_active=True)
        return queryset
    
    def filter_has_features(self, queryset, name, value):
        """
        Filter vehicles that have specific features.
        """
        if value:
            features = [feature.strip() for feature in value.split(',')]
            for feature in features:
                queryset = queryset.filter(features__icontains=feature)
        return queryset 