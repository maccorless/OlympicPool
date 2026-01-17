"""
SMS service for sending OTP codes via Twilio Verify.
"""
import logging
import secrets
import phonenumbers
from phonenumbers import NumberParseException
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from flask import current_app

logger = logging.getLogger(__name__)


def generate_otp():
    """Generate a 4-digit OTP code (for Dev/Local mode only)."""
    return str(secrets.randbelow(1000000)).zfill(4)


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


def send_verification_token(phone_number):
    """
    Send verification code via Twilio Verify.

    Args:
        phone_number: E.164 format (+12065551234)

    Returns:
        (success: bool, result: str)
        - In NO_SMS_MODE: (True, otp_code) for display
        - In production: (True, status) or (False, error_message)
    """
    # NO_SMS_MODE: Generate local OTP for display
    if current_app.config.get('NO_SMS_MODE'):
        otp_code = generate_otp()
        logger.info(f"NO_SMS_MODE: OTP for {phone_number}: {otp_code}")
        return True, otp_code

    # Production: Send via Twilio Verify
    account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
    auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
    service_sid = current_app.config.get('TWILIO_VERIFY_SERVICE_SID')

    if not all([account_sid, auth_token, service_sid]):
        logger.error("Twilio credentials or Service SID not configured")
        return False, "SMS service not configured"

    try:
        client = Client(account_sid, auth_token)
        verification = client.verify \
            .v2 \
            .services(service_sid) \
            .verifications \
            .create(to=phone_number, channel='sms')

        logger.info(f"Verification sent to {phone_number}, Status: {verification.status}")
        return True, verification.status

    except TwilioRestException as e:
        logger.error(f"Twilio API error sending to {phone_number}: {e}")
        return False, e.msg
    except Exception as e:
        logger.error(f"Failed to send verification to {phone_number}: {e}")
        return False, str(e)


def check_verification_token(phone_number, code):
    """
    Check verification code via Twilio Verify.

    Args:
        phone_number: E.164 format
        code: The code entered by user

    Returns:
        (success: bool, message: str)
    """
    # NO_SMS_MODE should be handled by caller (checking local DB), 
    # but as a safeguard we can return False if called unexpectedly, 
    # or implement a dummy check if we passed the hash? 
    # Actually, the caller handles NO_SMS_MODE logic for verification usually.
    # But let's support it if needed, though the caller has the state.
    if current_app.config.get('NO_SMS_MODE'):
         return False, "Cannot verify via Twilio in Dev Mode"

    account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
    auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
    service_sid = current_app.config.get('TWILIO_VERIFY_SERVICE_SID')

    if not all([account_sid, auth_token, service_sid]):
        return False, "Service not configured"

    try:
        client = Client(account_sid, auth_token)
        verification_check = client.verify \
            .v2 \
            .services(service_sid) \
            .verification_checks \
            .create(to=phone_number, code=code)

        if verification_check.status == 'approved':
            return True, "Verified"
        else:
            return False, "Invalid code"

    except TwilioRestException as e:
        logger.error(f"Twilio Verify check failed: {e}")
        return False, e.msg
    except Exception as e:
        logger.error(f"Error checking verification: {e}")
        return False, str(e)
