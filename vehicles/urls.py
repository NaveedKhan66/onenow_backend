"""
Vehicle URL patterns.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VehicleViewSet, VehicleSearchView

router = DefaultRouter()
router.register(r'', VehicleViewSet)

urlpatterns = [
    path('search/', VehicleSearchView.as_view(), name='vehicle-search'),
    path('', include(router.urls)),
] 