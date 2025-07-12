from django.contrib import admin
from django.utils.html import format_html
from .models import Vehicle, VehicleImage, VehicleReview


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('make', 'model', 'year', 'plate_number', 'status', 'daily_rate', 'owner')
    list_filter = ('make', 'status', 'fuel_type', 'transmission', 'body_type')
    search_fields = ('make', 'model', 'plate_number', 'owner__email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('owner', 'make', 'model', 'year', 'plate_number', 'color')
        }),
        ('Specifications', {
            'fields': ('fuel_type', 'transmission', 'body_type', 'engine_capacity', 'seating_capacity')
        }),
        ('Features & Pricing', {
            'fields': ('features', 'daily_rate', 'deposit_amount', 'mileage_limit')
        }),
        ('Status & Location', {
            'fields': ('status', 'pickup_location')
        }),
        ('Insurance & Registration', {
            'fields': ('insurance_policy_number', 'insurance_expiry', 'registration_expiry', 'last_service_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(VehicleImage)
class VehicleImageAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'image_preview', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('vehicle__make', 'vehicle__model', 'vehicle__plate_number')
    readonly_fields = ('created_at', 'image_preview')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px;"/>', obj.image.url)
        return "No image"
    image_preview.short_description = 'Preview'


@admin.register(VehicleReview)
class VehicleReviewAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'reviewer', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('vehicle__make', 'vehicle__model', 'reviewer__email', 'comment')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Review Information', {
            'fields': ('vehicle', 'reviewer', 'rating', 'comment')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
