"""
SMS service for sending OTP codes via Twilio.
"""
import logging
import secrets
import phonenumbers
from phonenumbers import NumberParseException
from twilio.rest import Client
from flask import current_app

logger = logging.getLogger(__name__)


def generate_otp():
    """Generate a 6-digit OTP code."""
    return str(secrets.randbelow(1000000)).zfill(6)


def validate_and_format_phone(phone_input, default_region='US'):
    """
    Validate and format phone number to E.164.

    Args:
        phone_input: User input (e.g., "206-555-1234" or "+12065551234")
        default_region: Default country code if not provided

    Returns:
        (valid: bool, formatted: str or None, error: str or None)
    """
    try:
        parsed = phonenumbers.parse(phone_input, default_region)

        if not phonenumbers.is_valid_number(parsed):
            return False, None, "Invalid phone number"

        # Format to E.164 (+12065551234)
        formatted = phonenumbers.format_number(
            parsed,
            phonenumbers.PhoneNumberFormat.E164
        )

        return True, formatted, None

    except NumberParseException as e:
        return False, None, str(e)


def send_otp_sms(phone_number, otp_code):
    """
    Send OTP code via Twilio SMS.

    Args:
        phone_number: E.164 format (+12065551234)
        otp_code: 6-digit string

    Returns:
        (success: bool, result: str)
        - In NO_SMS_MODE: (True, otp_code) for display
        - In production: (True, None) or (False, error_message)
    """
    # NO_SMS_MODE: return code for display on page
    if current_app.config.get('NO_SMS_MODE'):
        logger.info(f"NO_SMS_MODE: OTP for {phone_number}: {otp_code}")
        return True, otp_code

    # Production: send via Twilio
    if not current_app.config.get('TWILIO_ACCOUNT_SID'):
        logger.error("TWILIO_ACCOUNT_SID not configured")
        return False, "SMS service not configured"

    try:
        client = Client(
            current_app.config['TWILIO_ACCOUNT_SID'],
            current_app.config['TWILIO_AUTH_TOKEN']
        )

        message = client.messages.create(
            body=f"Your Olympic Medal Pool verification code is: {otp_code}\n\nThis code expires in 10 minutes.",
            from_=current_app.config['TWILIO_PHONE_NUMBER'],
            to=phone_number
        )

        logger.info(f"OTP SMS sent to {phone_number}, SID: {message.sid}")
        return True, None

    except Exception as e:
        logger.error(f"Failed to send SMS to {phone_number}: {e}")
        return False, str(e)
