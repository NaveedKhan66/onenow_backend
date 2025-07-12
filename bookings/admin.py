from django.contrib import admin
from .models import Booking, BookingCancellation, BookingPayment


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'customer_name', 'vehicle_info', 'start_date', 'end_date', 'status', 'payment_status', 'total_amount')
    list_filter = ('status', 'payment_status', 'start_date', 'end_date')
    search_fields = ('booking_id', 'customer_name', 'customer_email', 'vehicle__make', 'vehicle__model')
    readonly_fields = ('booking_id', 'created_at', 'updated_at', 'confirmed_at', 'cancelled_at')
    
    def vehicle_info(self, obj):
        return f"{obj.vehicle.make} {obj.vehicle.model} ({obj.vehicle.plate_number})"
    vehicle_info.short_description = 'Vehicle'
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_id', 'customer', 'vehicle', 'status', 'payment_status')
        }),
        ('Customer Details', {
            'fields': ('customer_name', 'customer_email', 'customer_phone', 'customer_address', 'driver_license_number')
        }),
        ('Dates & Times', {
            'fields': ('start_date', 'end_date', 'start_time', 'end_time')
        }),
        ('Pricing', {
            'fields': ('daily_rate', 'total_days', 'subtotal', 'deposit_amount', 'discount_amount', 'total_amount')
        }),
        ('Pickup & Return', {
            'fields': ('pickup_location', 'return_location', 'pickup_notes', 'return_notes')
        }),
        ('Additional Information', {
            'fields': ('special_requests', 'terms_accepted')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'cancelled_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(BookingCancellation)
class BookingCancellationAdmin(admin.ModelAdmin):
    list_display = ('booking', 'cancelled_by', 'refund_amount', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('booking__booking_id', 'booking__customer_name', 'reason')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Cancellation Details', {
            'fields': ('booking', 'cancelled_by', 'reason')
        }),
        ('Financial', {
            'fields': ('refund_amount', 'cancellation_fee')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )


@admin.register(BookingPayment)
class BookingPaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'payment_method', 'payment_type', 'amount', 'is_successful', 'processed_at')
    list_filter = ('payment_method', 'payment_type', 'is_successful', 'created_at')
    search_fields = ('booking__booking_id', 'transaction_id')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('booking', 'payment_method', 'payment_type', 'amount', 'currency')
        }),
        ('Transaction Details', {
            'fields': ('transaction_id', 'gateway_response', 'is_successful')
        }),
        ('Timestamps', {
            'fields': ('processed_at', 'created_at'),
            'classes': ('collapse',)
        })
    )
