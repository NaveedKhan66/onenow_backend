"""
Tests for vehicle functionality.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from vehicles.models import Vehicle, VehicleImage, VehicleReview

User = get_user_model()


class VehicleModelTest(TestCase):
    """
    Test cases for the Vehicle model.
    """
    
    def setUp(self):
        """
        Set up test data.
        """
        self.user = User.objects.create_user(
            email='owner@example.com',
            username='owner',
            password='testpassword123'
        )
        
        self.vehicle_data = {
            'owner': self.user,
            'make': 'Toyota',
            'model': 'Camry',
            'year': 2020,
            'plate_number': 'ABC123',
            'color': 'White',
            'fuel_type': 'petrol',
            'transmission': 'automatic',
            'body_type': 'sedan',
            'seating_capacity': 5,
            'daily_rate': Decimal('5000.00'),
            'deposit_amount': Decimal('10000.00'),
            'pickup_location': 'Downtown Lahore',
        }
    
    def test_vehicle_creation(self):
        """
        Test vehicle creation with valid data.
        """
        vehicle = Vehicle.objects.create(**self.vehicle_data)
        
        self.assertEqual(vehicle.make, self.vehicle_data['make'])
        self.assertEqual(vehicle.model, self.vehicle_data['model'])
        self.assertEqual(vehicle.year, self.vehicle_data['year'])
        self.assertEqual(vehicle.plate_number, self.vehicle_data['plate_number'])
        self.assertEqual(vehicle.daily_rate, self.vehicle_data['daily_rate'])
        self.assertTrue(vehicle.is_available)
        self.assertEqual(vehicle.status, 'available')
    
    def test_vehicle_string_representation(self):
        """
        Test vehicle string representation.
        """
        vehicle = Vehicle.objects.create(**self.vehicle_data)
        expected_str = f"{vehicle.year} {vehicle.make} {vehicle.model} ({vehicle.plate_number})"
        self.assertEqual(str(vehicle), expected_str)
    
    def test_vehicle_display_name(self):
        """
        Test vehicle display name property.
        """
        vehicle = Vehicle.objects.create(**self.vehicle_data)
        expected_display = f"{vehicle.make} {vehicle.model} ({vehicle.year})"
        self.assertEqual(vehicle.display_name, expected_display)
    
    def test_vehicle_is_available_property(self):
        """
        Test vehicle availability property.
        """
        vehicle = Vehicle.objects.create(**self.vehicle_data)
        
        # Initially available
        self.assertTrue(vehicle.is_available)
        
        # Set to rented
        vehicle.status = 'rented'
        vehicle.save()
        self.assertFalse(vehicle.is_available)
        
        # Set to inactive
        vehicle.status = 'available'
        vehicle.is_active = False
        vehicle.save()
        self.assertFalse(vehicle.is_available)
    
    def test_vehicle_review_creation(self):
        """
        Test vehicle review creation.
        """
        vehicle = Vehicle.objects.create(**self.vehicle_data)
        reviewer = User.objects.create_user(
            email='reviewer@example.com',
            username='reviewer',
            password='testpassword123'
        )
        
        review = VehicleReview.objects.create(
            vehicle=vehicle,
            reviewer=reviewer,
            rating=5,
            comment='Great car!'
        )
        
        self.assertEqual(review.vehicle, vehicle)
        self.assertEqual(review.reviewer, reviewer)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Great car!')
    
    def test_vehicle_image_creation(self):
        """
        Test vehicle image creation.
        """
        vehicle = Vehicle.objects.create(**self.vehicle_data)
        
        image = VehicleImage.objects.create(
            vehicle=vehicle,
            caption='Front view',
            is_primary=True
        )
        
        self.assertEqual(image.vehicle, vehicle)
        self.assertEqual(image.caption, 'Front view')
        self.assertTrue(image.is_primary)


class VehicleAPITest(APITestCase):
    """
    Test cases for vehicle API endpoints.
    """
    
    def setUp(self):
        """
        Set up test data.
        """
        self.client = APIClient()
        
        # Create users
        self.owner = User.objects.create_user(
            email='owner@example.com',
            username='owner',
            password='testpassword123'
        )
        
        self.customer = User.objects.create_user(
            email='customer@example.com',
            username='customer',
            password='testpassword123'
        )
        
        # Vehicle data
        self.vehicle_data = {
            'make': 'Toyota',
            'model': 'Camry',
            'year': 2020,
            'plate_number': 'ABC123',
            'color': 'White',
            'fuel_type': 'petrol',
            'transmission': 'automatic',
            'body_type': 'sedan',
            'seating_capacity': 5,
            'daily_rate': '5000.00',
            'deposit_amount': '10000.00',
            'pickup_location': 'Downtown Lahore',
        }
        
        # Create a vehicle
        self.vehicle = Vehicle.objects.create(
            owner=self.owner,
            make='Honda',
            model='Civic',
            year=2019,
            plate_number='XYZ789',
            color='Black',
            daily_rate=Decimal('4500.00'),
            deposit_amount=Decimal('8000.00'),
            pickup_location='Gulberg Lahore',
        )
    
    def test_vehicle_list_unauthorized(self):
        """
        Test vehicle list access without authentication.
        """
        url = reverse('vehicle-list')
        response = self.client.get(url)
        
        # Should be able to view vehicles without authentication
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_vehicle_creation_success(self):
        """
        Test successful vehicle creation.
        """
        self.client.force_authenticate(user=self.owner)
        url = reverse('vehicle-list')
        
        response = self.client.post(url, self.vehicle_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['make'], self.vehicle_data['make'])
        self.assertEqual(response.data['data']['model'], self.vehicle_data['model'])
        
        # Check if vehicle was created
        vehicle = Vehicle.objects.get(plate_number=self.vehicle_data['plate_number'])
        self.assertEqual(vehicle.owner, self.owner)
    
    def test_vehicle_creation_unauthorized(self):
        """
        Test vehicle creation without authentication.
        """
        url = reverse('vehicle-list')
        response = self.client.post(url, self.vehicle_data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_vehicle_creation_invalid_data(self):
        """
        Test vehicle creation with invalid data.
        """
        self.client.force_authenticate(user=self.owner)
        url = reverse('vehicle-list')
        
        # Invalid year
        invalid_data = self.vehicle_data.copy()
        invalid_data['year'] = 1800
        
        response = self.client.post(url, invalid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_vehicle_creation_duplicate_plate(self):
        """
        Test vehicle creation with duplicate plate number.
        """
        self.client.force_authenticate(user=self.owner)
        url = reverse('vehicle-list')
        
        # Use existing vehicle's plate number
        invalid_data = self.vehicle_data.copy()
        invalid_data['plate_number'] = self.vehicle.plate_number
        
        response = self.client.post(url, invalid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_vehicle_retrieve_success(self):
        """
        Test successful vehicle retrieval.
        """
        self.client.force_authenticate(user=self.owner)
        url = reverse('vehicle-detail', kwargs={'pk': self.vehicle.pk})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['id'], self.vehicle.pk)
    
    def test_vehicle_update_success(self):
        """
        Test successful vehicle update.
        """
        self.client.force_authenticate(user=self.owner)
        url = reverse('vehicle-detail', kwargs={'pk': self.vehicle.pk})
        
        update_data = {
            'color': 'Red',
            'daily_rate': '5500.00'
        }
        
        response = self.client.patch(url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['color'], 'Red')
        self.assertEqual(response.data['data']['daily_rate'], '5500.00')
        
        # Check if vehicle was updated
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.color, 'Red')
        self.assertEqual(self.vehicle.daily_rate, Decimal('5500.00'))
    
    def test_vehicle_update_unauthorized(self):
        """
        Test vehicle update by non-owner.
        """
        self.client.force_authenticate(user=self.customer)
        url = reverse('vehicle-detail', kwargs={'pk': self.vehicle.pk})
        
        update_data = {
            'color': 'Red'
        }
        
        response = self.client.patch(url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_vehicle_delete_success(self):
        """
        Test successful vehicle deletion (soft delete).
        """
        self.client.force_authenticate(user=self.owner)
        url = reverse('vehicle-detail', kwargs={'pk': self.vehicle.pk})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Check if vehicle was soft deleted
        self.vehicle.refresh_from_db()
        self.assertFalse(self.vehicle.is_active)
        self.assertEqual(self.vehicle.status, 'inactive')
    
    def test_vehicle_availability_check(self):
        """
        Test vehicle availability check.
        """
        self.client.force_authenticate(user=self.customer)
        url = reverse('vehicle-check-availability', kwargs={'pk': self.vehicle.pk})
        
        check_data = {
            'start_date': '2024-02-01',
            'end_date': '2024-02-03'
        }
        
        response = self.client.post(url, check_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('is_available', response.data['data'])
    
    def test_vehicle_search_filters(self):
        """
        Test vehicle search with filters.
        """
        url = reverse('vehicle-search')
        
        # Filter by make
        response = self.client.get(url, {'make': 'Honda'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Filter by price range
        response = self.client.get(url, {'daily_rate__gte': '4000', 'daily_rate__lte': '5000'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_my_vehicles_endpoint(self):
        """
        Test my vehicles endpoint.
        """
        self.client.force_authenticate(user=self.owner)
        url = reverse('vehicle-my-vehicles')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        # Should contain the owner's vehicle
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['id'], self.vehicle.pk)
    
    def test_vehicle_add_review(self):
        """
        Test adding a review to a vehicle.
        """
        self.client.force_authenticate(user=self.customer)
        url = reverse('vehicle-add-review', kwargs={'pk': self.vehicle.pk})
        
        review_data = {
            'rating': 5,
            'comment': 'Excellent car!'
        }
        
        response = self.client.post(url, review_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['rating'], 5)
        self.assertEqual(response.data['data']['comment'], 'Excellent car!')
        
        # Check if review was created
        review = VehicleReview.objects.get(vehicle=self.vehicle, reviewer=self.customer)
        self.assertEqual(review.rating, 5)
    
    def test_vehicle_duplicate_review(self):
        """
        Test adding duplicate review to a vehicle.
        """
        # Create initial review
        VehicleReview.objects.create(
            vehicle=self.vehicle,
            reviewer=self.customer,
            rating=4,
            comment='Good car'
        )
        
        self.client.force_authenticate(user=self.customer)
        url = reverse('vehicle-add-review', kwargs={'pk': self.vehicle.pk})
        
        review_data = {
            'rating': 5,
            'comment': 'Updated review'
        }
        
        response = self.client.post(url, review_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_vehicle_reviews_list(self):
        """
        Test listing vehicle reviews.
        """
        # Create a review
        VehicleReview.objects.create(
            vehicle=self.vehicle,
            reviewer=self.customer,
            rating=5,
            comment='Great car!'
        )
        
        url = reverse('vehicle-reviews', kwargs={'pk': self.vehicle.pk})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['rating'], 5) 