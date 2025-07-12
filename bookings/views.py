"""
Booking views for reservation management.
"""

from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from django.utils import timezone
from core.responses import StandardResponse
from core.permissions import IsOwner, IsOwnerOrReadOnly
from core.exceptions import BookingOverlapError, PaymentProcessingError
from .models import Booking, BookingPayment, BookingCancellation
from .serializers import (
    BookingCreateSerializer,
    BookingSerializer,
    BookingListSerializer,
    BookingUpdateSerializer,
    BookingPaymentSerializer,
    BookingCancellationSerializer,
    BookingAvailabilitySerializer,
    StripePaymentSerializer
)
from .filters import BookingFilter
from .services import StripePaymentService


class BookingViewSet(ModelViewSet):
    """
    ViewSet for booking CRUD operations.
    """
    queryset = Booking.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = BookingFilter
    search_fields = ['booking_id', 'customer_name', 'customer_email']
    ordering_fields = ['created_at', 'start_date', 'end_date', 'total_amount']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """
        Return appropriate serializer class based on action.
        """
        if self.action == 'create':
            return BookingCreateSerializer
        elif self.action == 'list':
            return BookingListSerializer
        elif self.action in ['update', 'partial_update']:
            return BookingUpdateSerializer
        return BookingSerializer
    
    def get_queryset(self):
        """
        Filter queryset based on user permissions.
        """
        user = self.request.user
        
        # Users can only see their own bookings
        return Booking.objects.filter(customer=user).select_related(
            'vehicle', 'customer'
        ).prefetch_related('payments', 'cancellation')
    
    def list(self, request, *args, **kwargs):
        """
        List user's bookings.
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return StandardResponse.success(
            data=serializer.data,
            message="Bookings retrieved successfully"
        )
    
    def create(self, request, *args, **kwargs):
        """
        Create a new booking.
        """
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            try:
                booking = serializer.save()
                response_serializer = BookingSerializer(booking)
                
                return StandardResponse.created(
                    data=response_serializer.data,
                    message="Booking created successfully"
                )
            except BookingOverlapError as e:
                return StandardResponse.error(
                    message=str(e),
                    error_code='BOOKING_OVERLAP',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return StandardResponse.error(
                    message="Failed to create booking",
                    errors={'booking': [str(e)]},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        return StandardResponse.error(
            message="Booking creation failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a specific booking.
        """
        booking = self.get_object()
        serializer = self.get_serializer(booking)
        
        return StandardResponse.success(
            data=serializer.data,
            message="Booking retrieved successfully"
        )
    
    def update(self, request, *args, **kwargs):
        """
        Update a booking.
        """
        partial = kwargs.pop('partial', False)
        booking = self.get_object()
        
        if not booking.can_be_modified:
            return StandardResponse.error(
                message="Booking cannot be modified at this time",
                error_code='BOOKING_NOT_MODIFIABLE',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(booking, data=request.data, partial=partial)
        
        if serializer.is_valid():
            try:
                serializer.save()
                response_serializer = BookingSerializer(booking)
                
                return StandardResponse.success(
                    data=response_serializer.data,
                    message="Booking updated successfully"
                )
            except Exception as e:
                return StandardResponse.error(
                    message="Failed to update booking",
                    errors={'booking': [str(e)]},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        return StandardResponse.error(
            message="Booking update failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    def partial_update(self, request, *args, **kwargs):
        """
        Partially update a booking.
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """
        Cancel a booking (soft delete).
        """
        booking = self.get_object()
        
        if not booking.can_be_cancelled:
            return StandardResponse.error(
                message="Booking cannot be cancelled at this time",
                error_code='BOOKING_NOT_CANCELLABLE',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', 'Cancelled by customer')
        booking.cancel_booking(reason)
        
        return StandardResponse.success(
            message="Booking cancelled successfully"
        )
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """
        Confirm a booking.
        """
        booking = self.get_object()
        
        if booking.status != 'pending':
            return StandardResponse.error(
                message="Only pending bookings can be confirmed",
                error_code='BOOKING_NOT_PENDING',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        booking.confirm_booking()
        serializer = BookingSerializer(booking)
        
        return StandardResponse.success(
            data=serializer.data,
            message="Booking confirmed successfully"
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a booking with reason.
        """
        booking = self.get_object()
        
        if not booking.can_be_cancelled:
            return StandardResponse.error(
                message="Booking cannot be cancelled at this time",
                error_code='BOOKING_NOT_CANCELLABLE',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', 'Cancelled by customer')
        booking.cancel_booking(reason)
        
        serializer = BookingSerializer(booking)
        
        return StandardResponse.success(
            data=serializer.data,
            message="Booking cancelled successfully"
        )
    
    @action(detail=True, methods=['post'])
    def start_rental(self, request, pk=None):
        """
        Start the rental (pickup).
        """
        booking = self.get_object()
        
        if booking.status != 'confirmed':
            return StandardResponse.error(
                message="Only confirmed bookings can be started",
                error_code='BOOKING_NOT_CONFIRMED',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        booking.start_rental()
        serializer = BookingSerializer(booking)
        
        return StandardResponse.success(
            data=serializer.data,
            message="Rental started successfully"
        )
    
    @action(detail=True, methods=['post'])
    def complete_rental(self, request, pk=None):
        """
        Complete the rental (return).
        """
        booking = self.get_object()
        
        if booking.status != 'ongoing':
            return StandardResponse.error(
                message="Only ongoing bookings can be completed",
                error_code='BOOKING_NOT_ONGOING',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        booking.complete_rental()
        serializer = BookingSerializer(booking)
        
        return StandardResponse.success(
            data=serializer.data,
            message="Rental completed successfully"
        )
    
    @action(detail=True, methods=['get'])
    def payments(self, request, pk=None):
        """
        Get all payments for a booking.
        """
        booking = self.get_object()
        payments = booking.payments.all()
        serializer = BookingPaymentSerializer(payments, many=True)
        
        return StandardResponse.success(
            data=serializer.data,
            message="Payments retrieved successfully"
        )
    
    @action(detail=True, methods=['post'])
    def add_payment(self, request, pk=None):
        """
        Add a payment to a booking.
        """
        booking = self.get_object()
        serializer = BookingPaymentSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(booking=booking)
            
            # Update booking payment status
            total_payments = sum(p.amount for p in booking.payments.filter(is_successful=True))
            if total_payments >= booking.total_amount:
                booking.payment_status = 'paid'
            elif total_payments > 0:
                booking.payment_status = 'partial'
            booking.save()
            
            return StandardResponse.created(
                data=serializer.data,
                message="Payment added successfully"
            )
        
        return StandardResponse.error(
            message="Payment addition failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def process_stripe_payment(self, request, pk=None):
        """
        Process Stripe payment for a booking.
        """
        booking = self.get_object()
        serializer = StripePaymentSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                payment_service = StripePaymentService()
                payment_result = payment_service.process_payment(
                    booking=booking,
                    payment_method_id=serializer.validated_data['payment_method_id'],
                    amount=serializer.validated_data['amount'],
                    currency=serializer.validated_data.get('currency', 'PKR')
                )
                
                return StandardResponse.success(
                    data=payment_result,
                    message="Payment processed successfully"
                )
            except PaymentProcessingError as e:
                return StandardResponse.error(
                    message=str(e),
                    error_code='PAYMENT_FAILED',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return StandardResponse.error(
                    message="Payment processing failed",
                    errors={'payment': [str(e)]},
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return StandardResponse.error(
            message="Invalid payment data",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def my_bookings(self, request):
        """
        Get current user's bookings with status filtering.
        """
        status_filter = request.query_params.get('status')
        queryset = self.get_queryset()
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = BookingListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = BookingListSerializer(queryset, many=True)
        return StandardResponse.success(
            data=serializer.data,
            message="Your bookings retrieved successfully"
        )
    
    @action(detail=False, methods=['post'])
    def check_availability(self, request):
        """
        Check vehicle availability for specific dates.
        """
        serializer = BookingAvailabilitySerializer(data=request.data)
        
        if serializer.is_valid():
            start_date = serializer.validated_data['start_date']
            end_date = serializer.validated_data['end_date']
            vehicle_id = request.data.get('vehicle_id')
            
            if not vehicle_id:
                return StandardResponse.error(
                    message="Vehicle ID is required",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Check for overlapping bookings
            overlapping_bookings = Booking.objects.filter(
                vehicle_id=vehicle_id,
                status__in=['confirmed', 'ongoing'],
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            
            is_available = not overlapping_bookings.exists()
            
            response_data = {
                'is_available': is_available,
                'start_date': start_date,
                'end_date': end_date,
                'vehicle_id': vehicle_id,
                'conflicting_bookings': overlapping_bookings.count()
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
