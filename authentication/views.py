"""
Authentication views for user management.
"""

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from core.responses import StandardResponse
from .models import User, UserProfile
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserProfileDetailSerializer,
    PasswordChangeSerializer
)


class UserRegistrationView(APIView):
    """
    API view for user registration.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Register a new user.
        """
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            user_data = UserProfileSerializer(user).data
            
            response_data = {
                'user': user_data,
                'tokens': {
                    'access': str(access_token),
                    'refresh': str(refresh),
                }
            }
            
            return StandardResponse.created(
                data=response_data,
                message="User registered successfully"
            )
        
        return StandardResponse.error(
            message="Registration failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class UserLoginView(APIView):
    """
    API view for user login.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Login user and return JWT tokens.
        """
        serializer = UserLoginSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            user_data = UserProfileSerializer(user).data
            
            response_data = {
                'user': user_data,
                'tokens': {
                    'access': str(access_token),
                    'refresh': str(refresh),
                }
            }
            
            return StandardResponse.success(
                data=response_data,
                message="Login successful"
            )
        
        return StandardResponse.error(
            message="Login failed",
            errors=serializer.errors,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class UserProfileView(RetrieveUpdateAPIView):
    """
    API view for user profile management.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """
        Return the current user.
        """
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):
        """
        Get user profile.
        """
        user = self.get_object()
        serializer = self.get_serializer(user)
        
        return StandardResponse.success(
            data=serializer.data,
            message="Profile retrieved successfully"
        )
    
    def update(self, request, *args, **kwargs):
        """
        Update user profile.
        """
        partial = kwargs.pop('partial', False)
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=partial)
        
        if serializer.is_valid():
            serializer.save()
            return StandardResponse.success(
                data=serializer.data,
                message="Profile updated successfully"
            )
        
        return StandardResponse.error(
            message="Profile update failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    def partial_update(self, request, *args, **kwargs):
        """
        Partially update user profile.
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class UserProfileDetailView(RetrieveUpdateAPIView):
    """
    API view for extended user profile management.
    """
    serializer_class = UserProfileDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """
        Return the current user's profile.
        """
        user_profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return user_profile
    
    def retrieve(self, request, *args, **kwargs):
        """
        Get extended user profile.
        """
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        
        return StandardResponse.success(
            data=serializer.data,
            message="Extended profile retrieved successfully"
        )
    
    def update(self, request, *args, **kwargs):
        """
        Update extended user profile.
        """
        partial = kwargs.pop('partial', False)
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data, partial=partial)
        
        if serializer.is_valid():
            serializer.save()
            return StandardResponse.success(
                data=serializer.data,
                message="Extended profile updated successfully"
            )
        
        return StandardResponse.error(
            message="Extended profile update failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    def partial_update(self, request, *args, **kwargs):
        """
        Partially update extended user profile.
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class PasswordChangeView(APIView):
    """
    API view for password change.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Change user password.
        """
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return StandardResponse.success(
                message="Password changed successfully"
            )
        
        return StandardResponse.error(
            message="Password change failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    Logout user by blacklisting the refresh token.
    """
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            
        return StandardResponse.success(
            message="Logout successful"
        )
    except Exception as e:
        return StandardResponse.error(
            message="Logout failed",
            errors={'refresh_token': ['Invalid token']},
            status_code=status.HTTP_400_BAD_REQUEST
        )
