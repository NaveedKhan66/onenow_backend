"""
Tests for authentication functionality.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from authentication.models import UserProfile

User = get_user_model()


class UserModelTest(TestCase):
    """
    Test cases for the User model.
    """
    
    def setUp(self):
        """
        Set up test data.
        """
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '+1234567890',
            'driver_license_number': 'DL123456',
            'address': '123 Test Street',
        }
    
    def test_user_creation(self):
        """
        Test user creation with valid data.
        """
        user = User.objects.create_user(
            email=self.user_data['email'],
            username=self.user_data['username'],
            first_name=self.user_data['first_name'],
            last_name=self.user_data['last_name'],
            password='testpassword123'
        )
        
        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.username, self.user_data['username'])
        self.assertEqual(user.get_full_name(), 'Test User')
        self.assertTrue(user.check_password('testpassword123'))
        self.assertFalse(user.is_profile_complete)
    
    def test_user_profile_creation(self):
        """
        Test user profile creation.
        """
        user = User.objects.create_user(
            email=self.user_data['email'],
            username=self.user_data['username'],
            password='testpassword123'
        )
        
        profile = UserProfile.objects.create(
            user=user,
            bio='Test bio',
            emergency_contact_name='Emergency Contact',
            emergency_contact_phone='+1234567890'
        )
        
        self.assertEqual(profile.user, user)
        self.assertEqual(profile.bio, 'Test bio')
        self.assertEqual(str(profile), f"Profile of {user.email}")
    
    def test_user_string_representation(self):
        """
        Test user string representation.
        """
        user = User.objects.create_user(
            email=self.user_data['email'],
            username=self.user_data['username'],
            first_name=self.user_data['first_name'],
            last_name=self.user_data['last_name'],
            password='testpassword123'
        )
        
        expected_str = f"{user.email} - {user.get_full_name()}"
        self.assertEqual(str(user), expected_str)


class AuthenticationAPITest(APITestCase):
    """
    Test cases for authentication API endpoints.
    """
    
    def setUp(self):
        """
        Set up test data.
        """
        self.client = APIClient()
        self.register_url = reverse('api-user-register')
        self.login_url = reverse('api-user-login')
        self.profile_url = reverse('api-user-profile')
        
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '+1234567890',
            'driver_license_number': 'DL123456',
            'address': '123 Test Street',
            'password': 'testpassword123',
            'password_confirm': 'testpassword123'
        }
    
    def test_user_registration_success(self):
        """
        Test successful user registration.
        """
        response = self.client.post(
            self.register_url, 
            self.user_data, 
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('user', response.data['data'])
        self.assertIn('tokens', response.data['data'])
        self.assertEqual(response.data['data']['user']['email'], self.user_data['email'])
        
        # Check if user was created
        user = User.objects.get(email=self.user_data['email'])
        self.assertEqual(user.username, self.user_data['username'])
    
    def test_user_registration_password_mismatch(self):
        """
        Test user registration with password mismatch.
        """
        self.user_data['password_confirm'] = 'wrongpassword'
        response = self.client.post(
            self.register_url, 
            self.user_data, 
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('password_confirm', response.data['errors'])
    
    def test_user_registration_duplicate_email(self):
        """
        Test user registration with duplicate email.
        """
        # Create first user
        User.objects.create_user(
            email=self.user_data['email'],
            username='firstuser',
            password='testpassword123'
        )
        
        # Try to create second user with same email
        response = self.client.post(
            self.register_url, 
            self.user_data, 
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('email', response.data['errors'])
    
    def test_user_login_success(self):
        """
        Test successful user login.
        """
        # Create user first
        user = User.objects.create_user(
            email=self.user_data['email'],
            username=self.user_data['username'],
            password=self.user_data['password']
        )
        
        login_data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        
        response = self.client.post(
            self.login_url, 
            login_data, 
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('user', response.data['data'])
        self.assertIn('tokens', response.data['data'])
        self.assertEqual(response.data['data']['user']['email'], self.user_data['email'])
    
    def test_user_login_invalid_credentials(self):
        """
        Test user login with invalid credentials.
        """
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(
            self.login_url, 
            login_data, 
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])
    
    def test_user_profile_retrieval(self):
        """
        Test user profile retrieval.
        """
        # Create user
        user = User.objects.create_user(
            email=self.user_data['email'],
            username=self.user_data['username'],
            password=self.user_data['password']
        )
        
        # Authenticate user
        self.client.force_authenticate(user=user)
        
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['email'], user.email)
    
    def test_user_profile_update(self):
        """
        Test user profile update.
        """
        # Create user
        user = User.objects.create_user(
            email=self.user_data['email'],
            username=self.user_data['username'],
            password=self.user_data['password']
        )
        
        # Authenticate user
        self.client.force_authenticate(user=user)
        
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone_number': '+9876543210'
        }
        
        response = self.client.patch(
            self.profile_url, 
            update_data, 
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['first_name'], 'Updated')
        self.assertEqual(response.data['data']['last_name'], 'Name')
        
        # Check if user was updated
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Updated')
        self.assertEqual(user.last_name, 'Name')
    
    def test_unauthorized_access(self):
        """
        Test unauthorized access to protected endpoints.
        """
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])
    
    def test_jwt_token_authentication(self):
        """
        Test JWT token authentication.
        """
        # Create user
        user = User.objects.create_user(
            email=self.user_data['email'],
            username=self.user_data['username'],
            password=self.user_data['password']
        )
        
        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['email'], user.email) 