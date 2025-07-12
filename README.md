# OneNow Backend - Car Rental Management System

A Django REST API backend for independent car rental companies, built for the 1Now developer case study.

## About 1Now

**1Now** builds software solutions for independent car rental companies. 1Now serves small to medium-scale car rental operators who need comprehensive software to manage their fleet operations online. This includes features like online booking systems, rental agreements, calendar management, and payment processing.

**Who it serves:** Independent car rental businesses like LahoreCarRental.com who need digital infrastructure to compete with larger companies by providing professional online booking experiences, automated management systems, and integrated payment solutions.

**Frontend Integration:** This backend API can connect to LahoreCarRental.com's frontend by providing RESTful endpoints for vehicle browsing, user registration/authentication, booking management, and payment processing. The frontend would make HTTP requests to these endpoints to display available cars, handle customer bookings, and process payments seamlessly.

## Project Overview

This Django REST Framework backend provides complete car rental management functionality including:

- **User Authentication & Management** - JWT-based authentication with user profiles
- **Vehicle Management** - CRUD operations for car fleet management
- **Booking System** - Comprehensive reservation management with overlap prevention
- **Payment Integration** - Stripe integration for secure payment processing
- **Advanced Features** - Filtering, search, reviews, and validation

## Technologies Used

- **Backend Framework:** Django 5.2.4 + Django REST Framework 3.16.0
- **Authentication:** JWT (djangorestframework-simplejwt)
- **Database:** SQLite (development) - easily configurable for PostgreSQL/MySQL
- **Payment Processing:** Stripe integration
- **Additional:** CORS headers, django-filter, Pillow for image handling

## Project Structure

```
onenow_backend/
├── authentication/          # User authentication and profile management
├── vehicles/               # Vehicle fleet management
├── bookings/              # Reservation and booking system
├── core/                  # Shared utilities and base classes
├── api/                   # API versioning structure
│   └── v1/               # Version 1 API endpoints
├── tests/                 # Comprehensive test suite
├── onenow_backend/        # Main Django project settings
└── requirements.txt       # Project dependencies
```

## Features

### ✅ Core Requirements

#### 1. User Authentication
- `POST /api/v1/auth/register/` - Register new user with JWT tokens
- `POST /api/v1/auth/login/` - Login with email/password, returns JWT tokens
- `GET /api/v1/auth/profile/` - Get current user profile
- `PATCH /api/v1/auth/profile/` - Update user profile
- `POST /api/v1/auth/logout/` - Logout and blacklist refresh token

#### 2. Vehicle Management
- `POST /api/v1/vehicles/` - Add new vehicle (owner only)
- `PUT /api/v1/vehicles/{id}/` - Update vehicle (owner only)
- `DELETE /api/v1/vehicles/{id}/` - Soft delete vehicle (owner only)
- `GET /api/v1/vehicles/` - List all available vehicles (public)
- `GET /api/v1/vehicles/{id}/` - Get vehicle details
- `GET /api/v1/vehicles/my_vehicles/` - Get user's vehicles

#### 3. Booking Management
- `POST /api/v1/bookings/` - Create new booking
- `GET /api/v1/bookings/` - List user's bookings
- `GET /api/v1/bookings/{id}/` - Get booking details
- `PATCH /api/v1/bookings/{id}/` - Update booking (if modifiable)
- `POST /api/v1/bookings/{id}/confirm/` - Confirm booking
- `POST /api/v1/bookings/{id}/cancel/` - Cancel booking

### ✨ Bonus Features

#### 1. Booking Overlap Prevention
- Automatic validation prevents double-booking of vehicles
- Real-time availability checking with `POST /api/v1/bookings/check_availability/`
- Comprehensive date conflict detection

#### 2. Stripe Payment Integration
- Mock Stripe payment processing: `POST /api/v1/bookings/{id}/process_stripe_payment/`
- Payment tracking and history: `GET /api/v1/bookings/{id}/payments/`
- Secure payment method handling

#### 3. Custom Validators
- Vehicle data validation (make, model, year, plate number)
- Booking date validation with business rules
- Phone number and license plate format validation
- Comprehensive input sanitization

#### 4. Advanced Query Filters
- Vehicle filtering: `GET /api/v1/vehicles/?make=Honda&daily_rate__lte=5000`
- Booking filtering: `GET /api/v1/bookings/?status=confirmed&from=2024-01-01`
- Search functionality across multiple fields
- Pagination support for large datasets

#### 5. Additional Features
- **Vehicle Reviews & Ratings:** Customer feedback system
- **Image Upload:** Multiple vehicle photos with primary image support
- **Comprehensive Logging:** Structured logging for monitoring
- **Error Handling:** Consistent error responses with proper HTTP status codes
- **Permissions System:** Role-based access control

## Installation & Setup

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Virtual environment (recommended)

### 1. Clone Repository
```bash
git clone <repository-url>
cd onenow_backend
```

### 2. Create Virtual Environment
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 6. Run Development Server
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

## Database Population (Testing)

To test the APIs with realistic data, you can populate the database with dummy data using the provided management command:

### Basic Usage
```bash
python manage.py populate_db
```

This will create:
- 10 sample users with complete profiles
- 15 sample vehicles with various makes, models, and features
- 20 sample bookings with different statuses
- Sample vehicle reviews and ratings

### Advanced Usage
```bash
# Specify custom counts
python manage.py populate_db --users 20 --vehicles 30 --bookings 50

# Clear existing data and populate fresh
python manage.py populate_db --clear --users 15 --vehicles 25 --bookings 40
```

### Command Options
- `--users N` - Number of users to create (default: 10)
- `--vehicles N` - Number of vehicles to create (default: 15)
- `--bookings N` - Number of bookings to create (default: 20)
- `--clear` - Clear existing data before populating

### Sample Data Includes
- **Users:** Realistic Pakistani names, addresses, phone numbers, and driver licenses
- **Vehicles:** Popular car brands (Toyota, Honda, BMW, etc.) with realistic pricing
- **Bookings:** Various booking statuses (confirmed, pending, completed, cancelled)
- **Reviews:** Customer reviews with ratings from 3-5 stars
- **Payments:** Sample payment records for completed bookings

**Note:** All users are created with password `testpass123` for easy testing.

### Testing Login Credentials
After populating the database, you can login with any of these sample emails:
- `ahmed.khan1@example.com`
- `fatima.ahmad2@example.com`
- `hassan.sheikh3@example.com`
- (and more...)

All users have the password: `testpass123`

## API Documentation

### Authentication Endpoints

#### Register User
```http
POST /api/v1/auth/register/
Content-Type: application/json

{
    "email": "user@example.com",
    "username": "username",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890",
    "driver_license_number": "DL123456",
    "address": "123 Main St, City",
    "password": "securepassword123",
    "password_confirm": "securepassword123"
}
```

**Response:**
```json
{
    "success": true,
    "message": "User registered successfully",
    "data": {
        "user": {
            "id": 1,
            "email": "user@example.com",
            "username": "username",
            "full_name": "John Doe",
            "is_verified": false
        },
        "tokens": {
            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
        }
    }
}
```

#### Login User
```http
POST /api/v1/auth/login/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "securepassword123"
}
```

### Vehicle Endpoints

#### Add Vehicle
```http
POST /api/v1/vehicles/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "make": "Toyota",
    "model": "Camry",
    "year": 2020,
    "plate_number": "ABC123",
    "color": "White",
    "fuel_type": "petrol",
    "transmission": "automatic",
    "body_type": "sedan",
    "seating_capacity": 5,
    "daily_rate": "5000.00",
    "deposit_amount": "10000.00",
    "pickup_location": "Downtown Lahore"
}
```

#### List Vehicles with Filters
```http
GET /api/v1/vehicles/?make=Toyota&daily_rate__lte=6000&seating_capacity__gte=4
```

### Booking Endpoints

#### Create Booking
```http
POST /api/v1/bookings/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "vehicle": 1,
    "start_date": "2024-02-01",
    "end_date": "2024-02-03",
    "customer_name": "John Doe",
    "customer_email": "john@example.com",
    "customer_phone": "+1234567890",
    "customer_address": "123 Main St",
    "driver_license_number": "DL123456",
    "pickup_location": "Downtown Lahore",
    "return_location": "Downtown Lahore",
    "terms_accepted": true
}
```

#### Check Availability
```http
POST /api/v1/bookings/check_availability/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "vehicle_id": 1,
    "start_date": "2024-02-01",
    "end_date": "2024-02-03"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Availability checked successfully",
    "data": {
        "is_available": true,
        "start_date": "2024-02-01",
        "end_date": "2024-02-03",
        "vehicle_id": 1,
        "conflicting_bookings": 0
    }
}
```

## Testing

### Run All Tests
```bash
python manage.py test
```

### Run Specific Test Modules
```bash
# Authentication tests
python manage.py test tests.test_authentication

# Vehicle tests  
python manage.py test tests.test_vehicles

# Booking tests
python manage.py test tests.test_bookings
```

### Test Coverage
The test suite includes **45+ comprehensive tests** covering:

- **Authentication:** User registration, login, profile management, JWT authentication
- **Vehicles:** CRUD operations, validation, permissions, search/filtering
- **Bookings:** Reservation creation, overlap prevention, status management, payments
- **Integration:** End-to-end API workflows
- **Edge Cases:** Error handling, validation, permission checking

## Error Handling

The API uses consistent error response format:

```json
{
    "success": false,
    "message": "Error description",
    "errors": {
        "field_name": ["Specific error details"]
    },
    "error_code": "SPECIFIC_ERROR_CODE"
}
```

### Common HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (permission denied)
- `404` - Not Found
- `500` - Internal Server Error

## Security Features

- **JWT Authentication:** Secure token-based authentication
- **Permission System:** Role-based access control
- **Input Validation:** Comprehensive data validation and sanitization
- **CORS Configuration:** Proper cross-origin resource sharing setup
- **SQL Injection Protection:** Django ORM provides built-in protection
- **XSS Prevention:** Automatic escaping of user input

## Deployment Considerations

### Environment Variables
Create a `.env` file with:
```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,api.your-domain.com
DATABASE_URL=postgresql://user:pass@localhost/dbname
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
```

### Production Database
Update `settings.py` for PostgreSQL:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'onenow_production',
        'USER': 'dbuser',
        'PASSWORD': 'dbpassword',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## License

This project is created for the 1Now developer case study and demonstration purposes.

---

## Contact

For questions about this implementation or 1Now's services, please reach out through the appropriate channels.

**Built with ❤️ for 1Now's Car Rental Platform** 