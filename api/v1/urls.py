"""
API v1 URL configuration.
"""

from django.urls import path, include

urlpatterns = [
    path('auth/', include('api.v1.authentication.urls')),
    
    path('vehicles/', include('api.v1.vehicles.urls')),
    
    path('bookings/', include('api.v1.bookings.urls')),
] 