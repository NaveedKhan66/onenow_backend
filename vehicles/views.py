"""
Vehicle views for CRUD operations.
"""

from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from core.responses import StandardResponse
from core.permissions import IsOwner, IsOwnerOrReadOnly
from .models import Vehicle, VehicleImage, VehicleReview
from .serializers import (
    VehicleSerializer,
    VehicleCreateSerializer,
    VehicleListSerializer,
    VehicleAvailabilitySerializer,
    VehicleImageSerializer,
    VehicleReviewSerializer
)
from .filters import VehicleFilter


class VehicleViewSet(ModelViewSet):
    """
    ViewSet for vehicle CRUD operations.
    """
    queryset = Vehicle.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = VehicleFilter
    search_fields = ['make', 'model', 'color', 'plate_number', 'pickup_location']
    ordering_fields = ['created_at', 'daily_rate', 'year', 'make', 'model']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """
        Return different permissions based on action.
        """
        if self.action == 'list':
            # Vehicle list is publicly accessible
            return [permissions.AllowAny()]
        elif self.action in ['reviews', 'check_availability']:
            # Public read actions that don't require authentication
            return [permissions.AllowAny()]
        elif self.action == 'add_review':
            # Write actions that require authentication
            return [permissions.IsAuthenticated()]
        else:
            # Default permissions for owner operations
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
    
    def get_serializer_class(self):
        """
        Return appropriate serializer class based on action.
        """
        if self.action == 'create':
            return VehicleCreateSerializer
        elif self.action == 'list':
            return VehicleListSerializer
        return VehicleSerializer
    
    def get_queryset(self):
        """
        Filter queryset based on user permissions.
        """
        if self.action == 'list':
            # List view shows all active vehicles
            return Vehicle.objects.filter(is_active=True).prefetch_related(
                'images', 'reviews', 'owner'
            )
        elif self.action in ['add_review', 'reviews', 'check_availability']:
            # Public actions that can be performed on any active vehicle
            return Vehicle.objects.filter(is_active=True).prefetch_related(
                'images', 'reviews', 'owner'
            )
        else:
            # Detail views show only user's vehicles
            return Vehicle.objects.filter(owner=self.request.user).prefetch_related(
                'images', 'reviews'
            )
    
    def list(self, request, *args, **kwargs):
        """
        List all available vehicles.
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            # Wrap pagination response in StandardResponse format
            return StandardResponse.success(
                data=paginated_response.data,
                message="Vehicles retrieved successfully"
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return StandardResponse.success(
            data=serializer.data,
            message="Vehicles retrieved successfully"
        )
    
    def create(self, request, *args, **kwargs):
        """
        Create a new vehicle.
        """
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            vehicle = serializer.save()
            response_serializer = VehicleSerializer(vehicle)
            
            return StandardResponse.created(
                data=response_serializer.data,
                message="Vehicle created successfully"
            )
        
        return StandardResponse.error(
            message="Vehicle creation failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a specific vehicle.
        """
        vehicle = self.get_object()
        serializer = self.get_serializer(vehicle)
        
        return StandardResponse.success(
            data=serializer.data,
            message="Vehicle retrieved successfully"
        )
    
    def update(self, request, *args, **kwargs):
        """
        Update a vehicle.
        """
        partial = kwargs.pop('partial', False)
        vehicle = self.get_object()
        serializer = self.get_serializer(vehicle, data=request.data, partial=partial)
        
        if serializer.is_valid():
            serializer.save()
            return StandardResponse.success(
                data=serializer.data,
                message="Vehicle updated successfully"
            )
        
        return StandardResponse.error(
            message="Vehicle update failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    def partial_update(self, request, *args, **kwargs):
        """
        Partially update a vehicle.
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a vehicle (soft delete by setting inactive).
        """
        vehicle = self.get_object()
        vehicle.is_active = False
        vehicle.status = 'inactive'
        vehicle.save()
        
        return StandardResponse.success(
            message="Vehicle deleted successfully"
        )
    
    @action(detail=True, methods=['post'])
    def check_availability(self, request, pk=None):
        """
        Check vehicle availability for specific dates.
        """
        vehicle = self.get_object()
        serializer = VehicleAvailabilitySerializer(data=request.data)
        
        if serializer.is_valid():
            start_date = serializer.validated_data['start_date']
            end_date = serializer.validated_data['end_date']
            
            # Check if vehicle is available for the given dates
            conflicting_bookings = vehicle.get_available_dates(start_date, end_date)
            
            is_available = not conflicting_bookings.exists()
            
            response_data = {
                'is_available': is_available,
                'start_date': start_date,
                'end_date': end_date,
                'conflicting_bookings': conflicting_bookings.count()
            }
            
            return StandardResponse.success(
                data=response_data,
                message="Availability checked successfully"
            )
        
        return StandardResponse.error(
            message="Invalid date range",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def upload_image(self, request, pk=None):
        """
        Upload image for a vehicle.
        """
        vehicle = self.get_object()
        serializer = VehicleImageSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(vehicle=vehicle)
            return StandardResponse.created(
                data=serializer.data,
                message="Image uploaded successfully"
            )
        
        return StandardResponse.error(
            message="Image upload failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['get'])
    def images(self, request, pk=None):
        """
        Get all images for a vehicle.
        """
        vehicle = self.get_object()
        images = vehicle.images.all()
        serializer = VehicleImageSerializer(images, many=True)
        
        return StandardResponse.success(
            data=serializer.data,
            message="Images retrieved successfully"
        )
    
    @action(detail=True, methods=['post'])
    def add_review(self, request, pk=None):
        """
        Add a review for a vehicle.
        """
        vehicle = self.get_object()
        serializer = VehicleReviewSerializer(data=request.data)
        
        if serializer.is_valid():
            # Check if user has already reviewed this vehicle
            if VehicleReview.objects.filter(vehicle=vehicle, reviewer=request.user).exists():
                return StandardResponse.error(
                    message="You have already reviewed this vehicle",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            serializer.save(vehicle=vehicle, reviewer=request.user)
            return StandardResponse.created(
                data=serializer.data,
                message="Review added successfully"
            )
        
        return StandardResponse.error(
            message="Review submission failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """
        Get all reviews for a vehicle.
        """
        vehicle = self.get_object()
        reviews = vehicle.reviews.all()
        serializer = VehicleReviewSerializer(reviews, many=True)
        
        return StandardResponse.success(
            data=serializer.data,
            message="Reviews retrieved successfully"
        )
    
    @action(detail=False, methods=['get'])
    def my_vehicles(self, request):
        """
        Get current user's vehicles.
        """
        vehicles = Vehicle.objects.filter(owner=request.user).prefetch_related(
            'images', 'reviews'
        )
        
        page = self.paginate_queryset(vehicles)
        if page is not None:
            serializer = VehicleSerializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            # Wrap pagination response in StandardResponse format
            return StandardResponse.success(
                data=paginated_response.data,
                message="Your vehicles retrieved successfully"
            )
        
        serializer = VehicleSerializer(vehicles, many=True)
        return StandardResponse.success(
            data=serializer.data,
            message="Your vehicles retrieved successfully"
        )


class VehicleSearchView(ListAPIView):
    """
    Advanced vehicle search view with filtering and sorting.
    """
    serializer_class = VehicleListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = VehicleFilter
    search_fields = ['make', 'model', 'color', 'pickup_location']
    ordering_fields = ['daily_rate', 'year', 'created_at']
    ordering = ['daily_rate']
    
    def get_queryset(self):
        """
        Return available vehicles for search.
        """
        return Vehicle.objects.filter(
            is_active=True,
            status='available'
        ).prefetch_related('images', 'reviews')
    
    def list(self, request, *args, **kwargs):
        """
        List available vehicles for search.
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            # Wrap pagination response in StandardResponse format
            return StandardResponse.success(
                data=paginated_response.data,
                message="Vehicles found"
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return StandardResponse.success(
            data=serializer.data,
            message="Vehicles found"
        )
