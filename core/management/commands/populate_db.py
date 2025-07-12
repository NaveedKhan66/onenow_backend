"""
Django management command to populate database with dummy data for testing.
"""

import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from vehicles.models import Vehicle, VehicleImage, VehicleReview
from bookings.models import Booking, BookingPayment

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate database with dummy data for testing APIs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Number of users to create (default: 10)'
        )
        parser.add_argument(
            '--vehicles',
            type=int,
            default=15,
            help='Number of vehicles to create (default: 15)'
        )
        parser.add_argument(
            '--bookings',
            type=int,
            default=20,
            help='Number of bookings to create (default: 20)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.clear_data()
        
        # Create users first
        users = self.create_users(options['users'])
        self.stdout.write(
            self.style.SUCCESS(f'Created {len(users)} users')
        )
        
        # Create vehicles
        vehicles = self.create_vehicles(users, options['vehicles'])
        self.stdout.write(
            self.style.SUCCESS(f'Created {len(vehicles)} vehicles')
        )
        
        # Create bookings
        bookings = self.create_bookings(users, vehicles, options['bookings'])
        self.stdout.write(
            self.style.SUCCESS(f'Created {len(bookings)} bookings')
        )
        
        # Create reviews
        reviews = self.create_reviews(users, vehicles)
        self.stdout.write(
            self.style.SUCCESS(f'Created {len(reviews)} reviews')
        )
        
        self.stdout.write(
            self.style.SUCCESS('Database populated successfully!')
        )

    def clear_data(self):
        """Clear existing data from the database."""
        self.stdout.write('Clearing existing data...')
        
        # Clear in reverse order of dependencies
        BookingPayment.objects.all().delete()
        Booking.objects.all().delete()
        VehicleReview.objects.all().delete()
        VehicleImage.objects.all().delete()
        Vehicle.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        
        self.stdout.write(self.style.SUCCESS('Existing data cleared'))

    def create_users(self, count):
        """Create sample users."""
        users = []
        
        # Sample user data
        first_names = ['Ahmed', 'Fatima', 'Hassan', 'Ayesha', 'Ali', 'Sara', 'Omar', 'Zara', 'Usman', 'Amina']
        last_names = ['Khan', 'Ahmad', 'Sheikh', 'Malik', 'Butt', 'Chaudhry', 'Qureshi', 'Siddiqui', 'Awan', 'Dar']
        cities = ['Lahore', 'Karachi', 'Islamabad', 'Faisalabad', 'Rawalpindi', 'Multan', 'Peshawar', 'Quetta']
        
        for i in range(count):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            city = random.choice(cities)
            
            user = User.objects.create_user(
                username=f'user{i+1}',
                email=f'{first_name.lower()}.{last_name.lower()}{i+1}@example.com',
                first_name=first_name,
                last_name=last_name,
                phone_number=f'+92-300-{random.randint(1000000, 9999999)}',
                date_of_birth=date(
                    random.randint(1980, 2000),
                    random.randint(1, 12),
                    random.randint(1, 28)
                ),
                driver_license_number=f'DL{random.randint(100000, 999999)}',
                address=f'House {random.randint(1, 999)}, Street {random.randint(1, 50)}, {city}, Pakistan',
                is_verified=True
            )
            user.set_password('testpass123')
            user.save()
            users.append(user)
            
        return users

    def create_vehicles(self, users, count):
        """Create sample vehicles."""
        vehicles = []
        
        # Sample vehicle data
        makes_models = [
            ('Toyota', ['Corolla', 'Camry', 'Prado', 'Hilux', 'Vitz']),
            ('Honda', ['Civic', 'City', 'Accord', 'CR-V', 'Vezel']),
            ('Suzuki', ['Alto', 'Cultus', 'Swift', 'Vitara', 'Wagon R']),
            ('Nissan', ['Sunny', 'X-Trail', 'Patrol', 'Altima', 'Micra']),
            ('Hyundai', ['Elantra', 'Tucson', 'Sonata', 'i10', 'i20']),
            ('Kia', ['Picanto', 'Sportage', 'Cerato', 'Stonic', 'Carnival']),
            ('BMW', ['3 Series', '5 Series', 'X3', 'X5', 'i8']),
            ('Mercedes', ['C-Class', 'E-Class', 'S-Class', 'GLE', 'GLA']),
        ]
        
        colors = ['White', 'Black', 'Silver', 'Gray', 'Blue', 'Red', 'Green', 'Brown']
        fuel_types = ['petrol', 'diesel', 'hybrid', 'electric', 'cng']
        transmissions = ['manual', 'automatic', 'semi_automatic']
        body_types = ['sedan', 'hatchback', 'suv', 'coupe', 'convertible']
        
        # Common vehicle features
        feature_sets = [
            ['Air Conditioning', 'Power Steering', 'Electric Windows'],
            ['Air Conditioning', 'Power Steering', 'Electric Windows', 'ABS', 'Airbags'],
            ['Air Conditioning', 'Power Steering', 'Electric Windows', 'ABS', 'Airbags', 'GPS Navigation'],
            ['Air Conditioning', 'Power Steering', 'Electric Windows', 'ABS', 'Airbags', 'GPS Navigation', 'Bluetooth', 'Backup Camera'],
            ['Air Conditioning', 'Power Steering', 'Electric Windows', 'ABS', 'Airbags', 'GPS Navigation', 'Bluetooth', 'Backup Camera', 'Leather Seats', 'Sunroof'],
        ]
        
        locations = ['DHA Lahore', 'Gulberg Lahore', 'Clifton Karachi', 'F-10 Islamabad', 'Bahria Town', 'Model Town']
        
        for i in range(count):
            make, models = random.choice(makes_models)
            model = random.choice(models)
            year = random.randint(2015, 2024)
            
            # Generate realistic plate number
            plate_number = f'{random.choice(["LHR", "KHI", "ISB", "RWP"])}-{random.randint(1000, 9999)}'
            
            # Calculate daily rate based on make and year
            base_rates = {
                'Toyota': 5000, 'Honda': 4800, 'Suzuki': 3500, 'Nissan': 4200,
                'Hyundai': 4000, 'Kia': 3800, 'BMW': 12000, 'Mercedes': 15000
            }
            base_rate = base_rates.get(make, 4000)
            year_multiplier = 1 + (year - 2015) * 0.1
            daily_rate = int(base_rate * year_multiplier)
            
            vehicle = Vehicle.objects.create(
                owner=random.choice(users),
                make=make,
                model=model,
                year=year,
                plate_number=plate_number,
                color=random.choice(colors),
                fuel_type=random.choice(fuel_types),
                transmission=random.choice(transmissions),
                body_type=random.choice(body_types),
                engine_capacity=round(random.uniform(1.0, 3.5), 1),
                seating_capacity=random.choice([2, 4, 5, 7, 8]),
                features=random.choice(feature_sets),
                daily_rate=daily_rate,
                deposit_amount=daily_rate * 2,  # 2 days deposit
                mileage_limit=random.choice([100, 150, 200, 300]),
                status=random.choice(['available', 'available', 'available', 'rented', 'maintenance']),
                insurance_policy_number=f'INS{random.randint(100000, 999999)}',
                insurance_expiry=date.today() + timedelta(days=random.randint(30, 365)),
                registration_expiry=date.today() + timedelta(days=random.randint(30, 365)),
                last_service_date=date.today() - timedelta(days=random.randint(1, 90)),
                pickup_location=random.choice(locations),
            )
            vehicles.append(vehicle)
            
        return vehicles

    def create_bookings(self, users, vehicles, count):
        """Create sample bookings."""
        bookings = []
        
        statuses = ['pending', 'confirmed', 'ongoing', 'completed', 'cancelled']
        payment_statuses = ['pending', 'paid', 'partial', 'refunded', 'failed']
        
        # Keep track of vehicle booking dates
        vehicle_bookings = {}  # vehicle_id -> list of (start_date, end_date) tuples
        
        for i in range(count):
            customer = random.choice(users)
            
            # Try to find an available vehicle and dates
            max_attempts = 10
            booking_created = False
            
            for _ in range(max_attempts):
                vehicle = random.choice(vehicles)
                
                # Generate booking dates
                start_date = date.today() + timedelta(days=random.randint(0, 60))
                end_date = start_date + timedelta(days=random.randint(1, 14))
                
                # Skip if dates are in the past for pending bookings
                booking_status = random.choice(statuses)
                if booking_status == 'pending' and start_date < date.today():
                    start_date = date.today() + timedelta(days=random.randint(1, 30))
                    end_date = start_date + timedelta(days=random.randint(1, 14))
                
                # Check if vehicle is available for these dates
                vehicle_dates = vehicle_bookings.get(vehicle.id, [])
                is_available = True
                
                for booked_start, booked_end in vehicle_dates:
                    if (start_date <= booked_end and end_date >= booked_start):
                        is_available = False
                        break
                
                if is_available:
                    # Add booking dates to vehicle_bookings
                    vehicle_bookings.setdefault(vehicle.id, []).append((start_date, end_date))
                    
                    booking = Booking.objects.create(
                        customer=customer,
                        vehicle=vehicle,
                        start_date=start_date,
                        end_date=end_date,
                        start_time=f'{random.randint(8, 10)}:00',
                        end_time=f'{random.randint(17, 19)}:00',
                        status=booking_status,
                        payment_status=random.choice(payment_statuses),
                        daily_rate=vehicle.daily_rate,
                        deposit_amount=vehicle.deposit_amount,
                        discount_amount=random.choice([0, 500, 1000, 1500]),
                        customer_name=customer.get_full_name(),
                        customer_email=customer.email,
                        customer_phone=customer.phone_number,
                        customer_address=customer.address,
                        driver_license_number=customer.driver_license_number,
                        pickup_location=vehicle.pickup_location,
                        return_location=vehicle.pickup_location,
                        pickup_notes=random.choice([
                            '', 'Please call upon arrival', 'Building has security gate',
                            'Park in visitor parking', 'Call 30 minutes before pickup'
                        ]),
                        special_requests=random.choice([
                            '', 'Need GPS navigation', 'Extra cleaning required',
                            'Child seat needed', 'Fuel tank full', 'Phone charger required'
                        ]),
                        terms_accepted=True,
                    )
                    bookings.append(booking)
                    booking_created = True
                    break
            
            if not booking_created:
                self.stdout.write(
                    self.style.WARNING(f'Could not create booking {i+1} after {max_attempts} attempts')
                )
        
        return bookings

    def create_reviews(self, users, vehicles):
        """Create sample vehicle reviews."""
        reviews = []
        
        review_comments = [
            'Great car, very comfortable and clean. Highly recommended!',
            'Excellent service and vehicle condition. Will rent again.',
            'Good value for money. The car was in perfect condition.',
            'Amazing experience! The car was fuel efficient and comfortable.',
            'Professional service. The vehicle was delivered on time.',
            'Clean and well-maintained vehicle. Great for city driving.',
            'Smooth ride and good fuel economy. Very satisfied.',
            'The car was exactly as described. No issues at all.',
            'Excellent customer service and quality vehicle.',
            'Would definitely recommend this car to others.',
            'Perfect for our family trip. Spacious and comfortable.',
            'Great car for the price. Very reliable and clean.',
        ]
        
        # Create reviews for random vehicles
        for vehicle in random.sample(vehicles, min(len(vehicles), 10)):
            # Create 1-3 reviews per vehicle
            for _ in range(random.randint(1, 3)):
                reviewer = random.choice(users)
                
                # Ensure reviewer hasn't already reviewed this vehicle
                if not VehicleReview.objects.filter(vehicle=vehicle, reviewer=reviewer).exists():
                    review = VehicleReview.objects.create(
                        vehicle=vehicle,
                        reviewer=reviewer,
                        rating=random.randint(3, 5),  # Mostly positive reviews
                        comment=random.choice(review_comments),
                    )
                    reviews.append(review)
        
        return reviews 