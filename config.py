# backend/config.py
import os
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# JWT
JWT_SECRET = os.getenv("SECRET_KEY")  # Changed from JWT_SECRET to SECRET_KEY to match .env
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))  # Changed to match .env

# Email
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# SMS (Optional - for production use)
SMS_API_KEY = os.getenv("SMS_API_KEY")
SMS_API_URL = os.getenv("SMS_API_URL")
SMS_SENDER_ID = os.getenv("SMS_SENDER_ID")

# Stripe
STRIPE_API_KEY = os.getenv("Secret_key")  # Use secret key for backend API calls
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Password Reset
RESET_TOKEN_EXPIRE_MINUTES = int(os.getenv("RESET_TOKEN_EXPIRE_MINUTES", "30"))  # default: 30 minutes

# App
PROJECT_NAME = "Doctor Appointment Booking System"
