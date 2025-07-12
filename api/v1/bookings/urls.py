"""
API v1 Bookings URL patterns.
"""

from django.urls import path, include

urlpatterns = [
    path('', include('bookings.urls')),
] 