"""
Authentication URL patterns.
"""

from django.urls import path
from .views import (
    UserRegistrationView,
    UserLoginView,
    UserProfileView,
    UserProfileDetailView,
    PasswordChangeView,
    logout_view
)

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('logout/', logout_view, name='user-logout'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile/detail/', UserProfileDetailView.as_view(), name='user-profile-detail'),
    path('password/change/', PasswordChangeView.as_view(), name='password-change'),
] 