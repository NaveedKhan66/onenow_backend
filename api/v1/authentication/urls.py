"""
API v1 Authentication URL patterns.
"""

from django.urls import path
from authentication.views import (
    UserRegistrationView,
    UserLoginView,
    UserProfileView,
    UserProfileDetailView,
    PasswordChangeView,
    logout_view
)

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='api-user-register'),
    path('login/', UserLoginView.as_view(), name='api-user-login'),
    path('logout/', logout_view, name='api-user-logout'),
    path('profile/', UserProfileView.as_view(), name='api-user-profile'),
    path('profile/detail/', UserProfileDetailView.as_view(), name='api-user-profile-detail'),
    path('password/change/', PasswordChangeView.as_view(), name='api-password-change'),
] 