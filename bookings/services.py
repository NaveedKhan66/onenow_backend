"""
Stripe payment service for processing payments.
"""

import stripe
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from core.exceptions import PaymentProcessingError
from .models import BookingPayment


class StripePaymentService:
    """
    Service class for handling Stripe payments.
    """
    
    def __init__(self):
        """
        Initialize Stripe with secret key.
        """
        stripe.api_key = settings.STRIPE_SECRET_KEY
    
    def process_payment(self, booking, payment_method_id, amount, currency='PKR'):
        """
        Process a payment using Stripe.
        """
        try:
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency.lower(),
                payment_method=payment_method_id,
                confirmation_method='manual',
                confirm=True,
                metadata={
                    'booking_id': booking.booking_id,
                    'customer_email': booking.customer_email,
                    'customer_name': booking.customer_name,
                }
            )
            
            # Check if payment was successful
            if intent.status == 'succeeded':
                # Create payment record
                payment = BookingPayment.objects.create(
                    booking=booking,
                    payment_method='stripe',
                    payment_type='full_payment',
                    amount=amount,
                    currency=currency,
                    transaction_id=intent.id,
                    gateway_response=intent,
                    is_successful=True,
                    processed_at=timezone.now()
                )
                
                # Update booking payment status
                total_payments = sum(
                    p.amount for p in booking.payments.filter(is_successful=True)
                )
                
                if total_payments >= booking.total_amount:
                    booking.payment_status = 'paid'
                elif total_payments > 0:
                    booking.payment_status = 'partial'
                
                booking.save()
                
                return {
                    'success': True,
                    'payment_id': payment.id,
                    'transaction_id': intent.id,
                    'amount': amount,
                    'currency': currency,
                    'status': 'succeeded'
                }
            
            elif intent.status == 'requires_action':
                # Payment requires additional action (3D Secure)
                return {
                    'success': False,
                    'requires_action': True,
                    'client_secret': intent.client_secret,
                    'status': 'requires_action'
                }
            
            else:
                # Payment failed
                raise PaymentProcessingError(f"Payment failed with status: {intent.status}")
        
        except stripe.error.CardError as e:
            # Card was declined
            raise PaymentProcessingError(f"Card declined: {e.user_message}")
        
        except stripe.error.RateLimitError as e:
            # Rate limit exceeded
            raise PaymentProcessingError("Payment processing rate limit exceeded. Please try again later.")
        
        except stripe.error.InvalidRequestError as e:
            # Invalid parameters
            raise PaymentProcessingError(f"Invalid payment request: {e.user_message}")
        
        except stripe.error.AuthenticationError as e:
            # Authentication failed
            raise PaymentProcessingError("Payment authentication failed. Please contact support.")
        
        except stripe.error.APIConnectionError as e:
            # Network communication failed
            raise PaymentProcessingError("Payment network error. Please try again later.")
        
        except stripe.error.StripeError as e:
            # Generic Stripe error
            raise PaymentProcessingError(f"Payment processing error: {e.user_message}")
        
        except Exception as e:
            # Unexpected error
            raise PaymentProcessingError(f"Unexpected payment error: {str(e)}")
    
    def create_refund(self, payment_intent_id, amount=None):
        """
        Create a refund for a payment.
        """
        try:
            refund = stripe.Refund.create(
                payment_intent=payment_intent_id,
                amount=int(amount * 100) if amount else None,
            )
            
            return {
                'success': True,
                'refund_id': refund.id,
                'amount': Decimal(refund.amount) / 100,
                'status': refund.status
            }
        
        except stripe.error.StripeError as e:
            raise PaymentProcessingError(f"Refund failed: {e.user_message}")
    
    def get_payment_intent(self, payment_intent_id):
        """
        Retrieve a payment intent from Stripe.
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return intent
        
        except stripe.error.StripeError as e:
            raise PaymentProcessingError(f"Failed to retrieve payment: {e.user_message}")
    
    def create_customer(self, email, name):
        """
        Create a Stripe customer.
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
            )
            return customer
        
        except stripe.error.StripeError as e:
            raise PaymentProcessingError(f"Failed to create customer: {e.user_message}")
    
    def create_payment_method(self, customer_id, payment_method_id):
        """
        Attach a payment method to a customer.
        """
        try:
            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id,
            )
            return True
        
        except stripe.error.StripeError as e:
            raise PaymentProcessingError(f"Failed to attach payment method: {e.user_message}")


class MockStripePaymentService:
    """
    Mock Stripe payment service for testing and development.
    """
    
    def process_payment(self, booking, payment_method_id, amount, currency='PKR'):
        """
        Mock payment processing.
        """
        # Simulate payment processing
        import random
        import uuid
        
        # Simulate success/failure (90% success rate)
        is_successful = random.random() > 0.1
        
        if is_successful:
            # Create mock payment record
            payment = BookingPayment.objects.create(
                booking=booking,
                payment_method='stripe',
                payment_type='full_payment',
                amount=amount,
                currency=currency,
                transaction_id=f"mock_{uuid.uuid4().hex[:16]}",
                gateway_response={
                    'id': f"pi_mock_{uuid.uuid4().hex[:16]}",
                    'status': 'succeeded',
                    'amount': int(amount * 100),
                    'currency': currency.lower(),
                    'mock': True
                },
                is_successful=True,
                processed_at=timezone.now()
            )
            
            # Update booking payment status
            total_payments = sum(
                p.amount for p in booking.payments.filter(is_successful=True)
            )
            
            if total_payments >= booking.total_amount:
                booking.payment_status = 'paid'
            elif total_payments > 0:
                booking.payment_status = 'partial'
            
            booking.save()
            
            return {
                'success': True,
                'payment_id': payment.id,
                'transaction_id': payment.transaction_id,
                'amount': amount,
                'currency': currency,
                'status': 'succeeded',
                'mock': True
            }
        else:
            raise PaymentProcessingError("Mock payment failed for testing purposes")
    
    def create_refund(self, payment_intent_id, amount=None):
        """
        Mock refund creation.
        """
        import uuid
        
        return {
            'success': True,
            'refund_id': f"re_mock_{uuid.uuid4().hex[:16]}",
            'amount': amount or Decimal('0.00'),
            'status': 'succeeded',
            'mock': True
        } 