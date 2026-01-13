"""
Configuration from environment variables.
"""
import os
from datetime import timedelta

# Flask secret key
SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-for-local-testing-only')

# Base URL for magic links
BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')

# Admin authorization (whitelist)
ADMIN_EMAILS = [email.strip() for email in os.getenv('ADMIN_EMAILS', '').split(',') if email.strip()]

# Resend API key (optional for dev)
RESEND_API_KEY = os.getenv('RESEND_API_KEY')

# Email from address
FROM_EMAIL = os.getenv('FROM_EMAIL', 'Olympic Medal Pool <noreply@yourdomain.com>')

# Dev mode: show magic links on page instead of sending email
NO_EMAIL_MODE = os.getenv('NO_EMAIL_MODE', 'True').lower() == 'true'

# Session configuration
PERMANENT_SESSION_LIFETIME = timedelta(days=21)
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Database
DATABASE = os.path.join(os.path.dirname(__file__), '..', 'instance', 'medal_pool.db')
