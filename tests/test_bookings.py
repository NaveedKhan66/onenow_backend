"""
Tests for booking functionality.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from bookings.models import Booking, BookingPayment, BookingCancellation
from vehicles.models import Vehicle

User = get_user_model()


class BookingModelTest(TestCase):
    """
    Test cases for the Booking model.
    """
    
    def setUp(self):
        """
        Set up test data.
        """
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
        
        self.vehicle = Vehicle.objects.create(
            owner=self.owner,
            make='Toyota',
            model='Camry',
            year=2020,
            plate_number='ABC123',
            color='White',
            daily_rate=Decimal('5000.00'),
            deposit_amount=Decimal('10000.00'),
            pickup_location='Downtown Lahore',
        )
        
        self.booking_data = {
            'customer': self.customer,
            'vehicle': self.vehicle,
            'start_date': date.today() + timedelta(days=1),
            'end_date': date.today() + timedelta(days=3),
            'daily_rate': Decimal('5000.00'),
            'deposit_amount': Decimal('10000.00'),
            'customer_name': 'John Doe',
            'customer_email': 'john@example.com',
            'customer_phone': '+1234567890',
            'customer_address': '123 Main St',
            'driver_license_number': 'DL123456',
            'pickup_location': 'Downtown Lahore',
            'return_location': 'Downtown Lahore',
            'terms_accepted': True,
        }
    
    def test_booking_creation(self):
        """
        Test booking creation with valid data.
        """
        booking = Booking.objects.create(**self.booking_data)
        
        self.assertEqual(booking.customer, self.customer)
        self.assertEqual(booking.vehicle, self.vehicle)
        self.assertEqual(booking.status, 'pending')
        self.assertEqual(booking.payment_status, 'pending')
        self.assertIsNotNone(booking.booking_id)
        self.assertTrue(booking.booking_id.startswith('BK'))
    
    def test_booking_amount_calculation(self):
        """
        Test booking amount calculation.
        """
        booking = Booking.objects.create(**self.booking_data)
        
        expected_days = (booking.end_date - booking.start_date).days
        expected_subtotal = booking.daily_rate * expected_days
        expected_total = expected_subtotal + booking.deposit_amount
        
        self.assertEqual(booking.total_days, expected_days)
        self.assertEqual(booking.subtotal, expected_subtotal)
        self.assertEqual(booking.total_amount, expected_total)
    
    def test_booking_string_representation(self):
        """
        Test booking string representation.
        """
        booking = Booking.objects.create(**self.booking_data)
        expected_str = f"Booking {booking.booking_id} - {booking.customer_name}"
        self.assertEqual(str(booking), expected_str)
    
    def test_booking_duration_property(self):
        """
        Test booking duration property.
        """
        booking = Booking.objects.create(**self.booking_data)
        expected_duration = (booking.end_date - booking.start_date).days
        self.assertEqual(booking.duration_days, expected_duration)
    
    def test_booking_is_active_property(self):
        """
        Test booking is_active property.
        """
        booking = Booking.objects.create(**self.booking_data)
        
        # Initially pending, not active
        self.assertFalse(booking.is_active)
        
        # Confirmed, should be active
        booking.status = 'confirmed'
        booking.save()
        self.assertTrue(booking.is_active)
        
        # Ongoing, should be active
        booking.status = 'ongoing'
        booking.save()
        self.assertTrue(booking.is_active)
        
        # Completed, not active
        booking.status = 'completed'
        booking.save()
        self.assertFalse(booking.is_active)
    
    def test_booking_can_be_cancelled_property(self):
        """
        Test booking can_be_cancelled property.
        """
        # Future booking
        future_booking_data = self.booking_data.copy()
        future_booking_data['start_date'] = date.today() + timedelta(days=5)
        future_booking_data['end_date'] = date.today() + timedelta(days=7)
        
        booking = Booking.objects.create(**future_booking_data)
        self.assertTrue(booking.can_be_cancelled)
        
        # Past booking - create with valid dates first, then update to past dates
        past_booking_data = self.booking_data.copy()
        past_booking_data['start_date'] = date.today() + timedelta(days=10)
        past_booking_data['end_date'] = date.today() + timedelta(days=12)
        
        past_booking = Booking.objects.create(**past_booking_data)
        # Update to past dates bypassing validation
        Booking.objects.filter(pk=past_booking.pk).update(
            start_date=date.today() - timedelta(days=3),
            end_date=date.today() - timedelta(days=1)
        )
        past_booking.refresh_from_db()
        self.assertFalse(past_booking.can_be_cancelled)
    
    def test_booking_confirm_method(self):
        """
        Test booking confirm method.
        """
        booking = Booking.objects.create(**self.booking_data)
        
        self.assertEqual(booking.status, 'pending')
        self.assertIsNone(booking.confirmed_at)
        
        booking.confirm_booking()
        
        self.assertEqual(booking.status, 'confirmed')
        self.assertIsNotNone(booking.confirmed_at)
    
    def test_booking_cancel_method(self):
        """
        Test booking cancel method.
        """
        # Future booking
        future_booking_data = self.booking_data.copy()
        future_booking_data['start_date'] = date.today() + timedelta(days=5)
        future_booking_data['end_date'] = date.today() + timedelta(days=7)
        
        booking = Booking.objects.create(**future_booking_data)
        
        self.assertEqual(booking.status, 'pending')
        self.assertIsNone(booking.cancelled_at)
        
        booking.cancel_booking('Customer requested cancellation')
        
        self.assertEqual(booking.status, 'cancelled')
        self.assertIsNotNone(booking.cancelled_at)
        
        # Check if cancellation record was created
        cancellation = BookingCancellation.objects.get(booking=booking)
        self.assertEqual(cancellation.reason, 'Customer requested cancellation')
    
    def test_booking_payment_creation(self):
        """
        Test booking payment creation.
        """
        booking = Booking.objects.create(**self.booking_data)
        
        payment = BookingPayment.objects.create(
            booking=booking,
            payment_method='stripe',
            payment_type='full_payment',
            amount=booking.total_amount,
            currency='PKR',
            transaction_id='test_transaction_123',
            is_successful=True,
            processed_at=timezone.now()
        )
        
        self.assertEqual(payment.booking, booking)
        self.assertEqual(payment.amount, booking.total_amount)
        self.assertTrue(payment.is_successful)


class BookingAPITest(APITestCase):
    """
    Test cases for booking API endpoints.
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
        
        # Create vehicle
        self.vehicle = Vehicle.objects.create(
            owner=self.owner,
            make='Toyota',
            model='Camry',
            year=2020,
            plate_number='ABC123',
            color='White',
            daily_rate=Decimal('5000.00'),
            deposit_amount=Decimal('10000.00'),
            pickup_location='Downtown Lahore',
        )
        
        # Booking data
        self.booking_data = {
            'vehicle': self.vehicle.id,
            'start_date': (date.today() + timedelta(days=2)).isoformat(),
            'end_date': (date.today() + timedelta(days=4)).isoformat(),
            'customer_name': 'John Doe',
            'customer_email': 'john@example.com',
            'customer_phone': '+1234567890',
            'customer_address': '123 Main St',
            'driver_license_number': 'DL123456',
            'pickup_location': 'Downtown Lahore',
            'return_location': 'Downtown Lahore',
            'terms_accepted': True,
        }
        
        # Create a booking
        self.booking = Booking.objects.create(
            customer=self.customer,
            vehicle=self.vehicle,
            start_date=date.today() + timedelta(days=2),
            end_date=date.today() + timedelta(days=4),
            daily_rate=self.vehicle.daily_rate,
            deposit_amount=self.vehicle.deposit_amount,
            customer_name='John Doe',
            customer_email='john@example.com',
            customer_phone='+1234567890',
            customer_address='123 Main St',
            driver_license_number='DL123456',
            pickup_location='Downtown Lahore',
            return_location='Downtown Lahore',
            terms_accepted=True,
        )
    
    def test_booking_creation_success(self):
        """
        Test successful booking creation.
        """
        self.client.force_authenticate(user=self.customer)
        url = reverse('booking-list')
        
        response = self.client.post(url, self.booking_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['customer'], self.customer.id)
        self.assertEqual(response.data['data']['vehicle'], self.vehicle.id)
        
        # Check if booking was created
        booking = Booking.objects.get(booking_id=response.data['data']['booking_id'])
        self.assertEqual(booking.customer, self.customer)
    
    def test_booking_creation_unauthorized(self):
        """
        Test booking creation without authentication.
        """
        url = reverse('booking-list')
        response = self.client.post(url, self.booking_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_booking_creation_invalid_dates(self):
        """
        Test booking creation with invalid dates.
        """
        self.client.force_authenticate(user=self.customer)
        url = reverse('booking-list')
        
        # End date before start date
        invalid_data = self.booking_data.copy()
        invalid_data['start_date'] = (date.today() + timedelta(days=5)).isoformat()
        invalid_data['end_date'] = (date.today() + timedelta(days=3)).isoformat()
        
        response = self.client.post(url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_booking_creation_past_dates(self):
        """
        Test booking creation with past dates.
        """
        self.client.force_authenticate(user=self.customer)
        url = reverse('booking-list')
        
        # Past dates
        invalid_data = self.booking_data.copy()
        invalid_data['start_date'] = (date.today() - timedelta(days=2)).isoformat()
        invalid_data['end_date'] = (date.today() - timedelta(days=1)).isoformat()
        
        response = self.client.post(url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_booking_creation_without_terms(self):
        """
        Test booking creation without accepting terms.
        """
        self.client.force_authenticate(user=self.customer)
        url = reverse('booking-list')
        
        invalid_data = self.booking_data.copy()
        invalid_data['terms_accepted'] = False
        
        response = self.client.post(url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('terms_accepted', response.data['errors'])
    
    def test_booking_list_success(self):
        """
        Test successful booking list retrieval.
        """
        self.client.force_authenticate(user=self.customer)
        url = reverse('booking-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        # Response data contains pagination structure
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['id'], self.booking.id)
    
    def test_booking_retrieve_success(self):
        """
        Test successful booking retrieval.
        """
        self.client.force_authenticate(user=self.customer)
        url = reverse('booking-detail', kwargs={'pk': self.booking.pk})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['id'], self.booking.id)
    
    def test_booking_retrieve_unauthorized(self):
        """
        Test booking retrieval by non-owner.
        """
        self.client.force_authenticate(user=self.owner)
        url = reverse('booking-detail', kwargs={'pk': self.booking.pk})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_booking_update_success(self):
        """
        Test successful booking update.
        """
        self.client.force_authenticate(user=self.customer)
        url = reverse('booking-detail', kwargs={'pk': self.booking.pk})
        
        update_data = {
            'customer_name': 'Jane Doe',
            'customer_phone': '+9876543210'
        }
        
        response = self.client.patch(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['customer_name'], 'Jane Doe')
        self.assertEqual(response.data['data']['customer_phone'], '+9876543210')
        
        # Check if booking was updated
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.customer_name, 'Jane Doe')
        self.assertEqual(self.booking.customer_phone, '+9876543210')
    
    def test_booking_confirm_success(self):
        """
        Test successful booking confirmation.
        """
        self.client.force_authenticate(user=self.customer)
        url = reverse('booking-confirm', kwargs={'pk': self.booking.pk})
        
        response = self.client.post(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['status'], 'confirmed')
        
        # Check if booking was confirmed
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'confirmed')
        self.assertIsNotNone(self.booking.confirmed_at)
    
    def test_booking_cancel_success(self):
        """
        Test successful booking cancellation.
        """
        # Create future booking
        future_booking = Booking.objects.create(
            customer=self.customer,
            vehicle=self.vehicle,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=12),
            daily_rate=self.vehicle.daily_rate,
            deposit_amount=self.vehicle.deposit_amount,
            customer_name='John Doe',
            customer_email='john@example.com',
            customer_phone='+1234567890',
            customer_address='123 Main St',
            driver_license_number='DL123456',
            pickup_location='Downtown Lahore',
            return_location='Downtown Lahore',
            terms_accepted=True,
        )
        
        self.client.force_authenticate(user=self.customer)
        url = reverse('booking-cancel', kwargs={'pk': future_booking.pk})
        
        cancel_data = {
            'reason': 'Changed plans'
        }
        
        response = self.client.post(url, cancel_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['status'], 'cancelled')
        
        # Check if booking was cancelled
        future_booking.refresh_from_db()
        self.assertEqual(future_booking.status, 'cancelled')
        self.assertIsNotNone(future_booking.cancelled_at)
    
    def test_booking_availability_check(self):
        """
        Test booking availability check.
        """
        self.client.force_authenticate(user=self.customer)
        url = reverse('booking-check-availability')
        
        # Check availability for different dates
        check_data = {
            'vehicle_id': self.vehicle.id,
            'start_date': (date.today() + timedelta(days=10)).isoformat(),
            'end_date': (date.today() + timedelta(days=12)).isoformat(),
        }
        
        response = self.client.post(url, check_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('is_available', response.data['data'])
        self.assertTrue(response.data['data']['is_available'])
    
    def test_booking_availability_check_conflict(self):
        """
        Test booking availability check with conflict.
        """
        # Confirm existing booking
        self.booking.status = 'confirmed'
        self.booking.save()
        
        self.client.force_authenticate(user=self.customer)
        url = reverse('booking-check-availability')
        
        # Check availability for overlapping dates
        check_data = {
            'vehicle_id': self.vehicle.id,
            'start_date': (date.today() + timedelta(days=2)).isoformat(),
            'end_date': (date.today() + timedelta(days=4)).isoformat(),
        }
        
        response = self.client.post(url, check_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('is_available', response.data['data'])
        self.assertFalse(response.data['data']['is_available'])
    
    def test_booking_my_bookings_endpoint(self):
        """
        Test my bookings endpoint.
        """
        self.client.force_authenticate(user=self.customer)
        url = reverse('booking-my-bookings')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        # Response data contains pagination structure
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['id'], self.booking.id)
    
    def test_booking_add_payment(self):
        """
        Test adding payment to booking.
        """
        self.client.force_authenticate(user=self.customer)
        url = reverse('booking-add-payment', kwargs={'pk': self.booking.pk})
        
        payment_data = {
            'payment_method': 'stripe',
            'payment_type': 'full_payment',
            'amount': str(self.booking.total_amount),
            'currency': 'PKR',
            'is_successful': True
        }
        
        response = self.client.post(url, payment_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['amount'], str(self.booking.total_amount))
        
        # Check if payment was created
        payment = BookingPayment.objects.get(booking=self.booking)
        self.assertEqual(payment.amount, self.booking.total_amount)
    
    def test_booking_payments_list(self):
        """
        Test listing booking payments.
        """
        # Create a payment
        BookingPayment.objects.create(
            booking=self.booking,
            payment_method='stripe',
            payment_type='full_payment',
            amount=self.booking.total_amount,
            currency='PKR',
            is_successful=True
        )
        
        self.client.force_authenticate(user=self.customer)
        url = reverse('booking-payments', kwargs={'pk': self.booking.pk})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        # This endpoint returns a list directly, not paginated
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['amount'], str(self.booking.total_amount)) 