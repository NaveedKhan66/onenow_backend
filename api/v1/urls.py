"""
API v1 URL configuration.
"""

from django.urls import path, include

urlpatterns = [
    # Authentication endpoints
    path('auth/', include('api.v1.authentication.urls')),
    
    # Vehicle management endpoints
    path('vehicles/', include('api.v1.vehicles.urls')),
    
    # Booking management endpoints
    path('bookings/', include('api.v1.bookings.urls')),
] 