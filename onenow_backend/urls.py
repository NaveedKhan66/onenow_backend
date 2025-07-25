"""
URL configuration for onenow_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger Schema View Configuration
schema_view = get_schema_view(
    openapi.Info(
        title="OneNow Backend API",
        default_version='v1',
        description="""
        OneNow Backend - Car Rental Management System
        
        A comprehensive Django REST API for independent car rental companies.
        
        Features:
        - User Authentication & Management (JWT-based)
        - Vehicle Fleet Management (CRUD operations)
        - Booking System (reservations with overlap prevention)
        - Payment Integration (Stripe)
        - Advanced Query Filters & Search
        - Vehicle Reviews & Ratings
        
        This API serves as the backend for car rental platforms like LahoreCarRental.com,
        providing professional online booking experiences and automated management systems.
        """,
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="support@onenow.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API routes
    path('api/v1/', include('api.v1.urls')),
    
    # App-specific routes
    path('auth/', include('authentication.urls')),
    
    # Swagger/OpenAPI documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API documentation root
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui-root'),
]
