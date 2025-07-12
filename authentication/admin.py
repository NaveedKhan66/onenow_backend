from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_verified')
    list_filter = UserAdmin.list_filter + ('is_verified',)
    fieldsets = UserAdmin.fieldsets + (
        ('Verification', {'fields': ('is_verified',)}),
    )
    
    def is_verified(self, obj):
        try:
            return obj.profile.is_verified
        except UserProfile.DoesNotExist:
            return False
    is_verified.boolean = True
    is_verified.short_description = 'Verified'


admin.site.register(User, CustomUserAdmin)
