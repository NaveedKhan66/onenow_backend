"""
Authentication serializers for user management.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, UserProfile


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'username', 'first_name', 'last_name',
            'phone_number', 'date_of_birth', 'driver_license_number',
            'address', 'password', 'password_confirm'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, attrs):
        """
        Validate password confirmation and other fields.
        """
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        if password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': 'Password confirmation does not match.'
            })
        
        # Remove password_confirm from attrs as it's not a model field
        attrs.pop('password_confirm', None)
        
        return attrs
    
    def validate_email(self, value):
        """
        Validate email uniqueness.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists.')
        return value
    
    def validate_username(self, value):
        """
        Validate username uniqueness.
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Username already exists.')
        return value
    
    def create(self, validated_data):
        """
        Create user with encrypted password.
        """
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )
    
    def validate(self, attrs):
        """
        Validate user credentials.
        """
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    'Invalid email or password.',
                    code='authorization'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled.',
                    code='authorization'
                )
            
            attrs['user'] = user
            return attrs
        
        raise serializers.ValidationError(
            'Must include email and password.',
            code='authorization'
        )


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    is_profile_complete = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'phone_number', 'date_of_birth',
            'driver_license_number', 'address', 'is_verified',
            'is_profile_complete', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'email', 'username', 'is_verified', 'created_at', 'updated_at']


class UserProfileDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for extended user profile information.
    """
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'user', 'avatar', 'bio', 'emergency_contact_name',
            'emergency_contact_phone', 'preferred_language'
        ]


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change.
    """
    old_password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_old_password(self, value):
        """
        Validate current password.
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value
    
    def validate(self, attrs):
        """
        Validate password confirmation.
        """
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        
        if new_password != new_password_confirm:
            raise serializers.ValidationError({
                'new_password_confirm': 'Password confirmation does not match.'
            })
        
        return attrs
    
    def save(self, **kwargs):
        """
        Save new password.
        """
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user 