"""
Configuration from environment variables.
"""
import os
from datetime import timedelta

# Flask secret key
SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-for-local-testing-only')

# Debug mode (auto-reload on code changes)
DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# Base URL for magic links
BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')

# Admin authorization (whitelist) - normalized to lowercase for case-insensitive comparison
ADMIN_EMAILS = [email.strip().lower() for email in os.getenv('ADMIN_EMAILS', '').split(',') if email.strip()]

# Twilio configuration for SMS OTP
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_VERIFY_SERVICE_SID = os.getenv('TWILIO_VERIFY_SERVICE_SID')

# Dev mode: show OTP on page instead of sending SMS
NO_SMS_MODE = os.getenv('NO_SMS_MODE', 'True').lower() == 'true'

# Session configuration
# Sessions valid until end of contest (March 31, 2026)
# Calculate days from now to end of contest (with buffer for early deployments)
from datetime import datetime
_contest_end = datetime(2026, 3, 31, 23, 59, 59)
_days_until_end = (_contest_end - datetime.now()).days + 1
PERMANENT_SESSION_LIFETIME = timedelta(days=max(_days_until_end, 365))  # At least 1 year
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Database
# Use Railway volume path if available, otherwise local instance folder
DATABASE_DIR = os.getenv('DATABASE_DIR', os.path.join(os.path.dirname(__file__), '..', 'instance'))
DATABASE = os.path.join(DATABASE_DIR, 'medal_pool.db')
