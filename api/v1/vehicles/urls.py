"""
API v1 Vehicles URL patterns.
"""

from django.urls import path, include

urlpatterns = [
    path('', include('vehicles.urls')),
] 