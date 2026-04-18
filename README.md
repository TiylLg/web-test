# Website Backend API

FastAPI backend for the website with authentication functionality.

## Features

- **Sign Up**: User registration with email verification
- **Login**: User authentication with JWT tokens
- **Verify**: Token verification endpoint
- **Renew**: Token renewal endpoint
- **MongoDB Integration**: Uses WebsiteDB database with Account and Verification collections


## Setup

### 1. Create Virtual Environment
```bash
python -m venv venv
```

### 2. Activate Virtual Environment
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
1. Copy `env_template.txt` to `.env`
2. Update the environment variables with your actual values:
   - MongoDB connection details
   - JWT secret key

### 5. Run the Application
```bash
uvicorn app.main:app --reload
```

The API will be available at: http://localhost:8000

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

### Authentication
- `POST /api/v1/signup` - User registration
- `POST /api/v1/login` - User login
- `POST /api/v1/verify` - Verify JWT token
- `POST /api/v1/renew` - Renew JWT token
- `POST /api/v1/logout` - User logout
- `POST /api/v1/reset-password` - Reset password

### Verification
- `POST /api/v1/send-verification` - Send verification code
- `POST /api/v1/verify-code` - Verify code

### Health
- `GET /api/v1/health` - Health check

## Database Structure

### Account Collection
- Email
- Password (hashed)
- Username
- Phone
- CreatedAt
- SessionID
- IsActive

### Verification Collection
- Email
- VerificationCode
- CreatedAt
- IsUsed
- ExpiresAt

## Docker

Build and run with Docker:
```bash
docker build -t website-backend .
docker run -p 8000:8000 website-backend
```
