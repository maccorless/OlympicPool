"""
Authentication routes: register, login, OTP verification, logout.
SMS OTP sending logic uses Twilio (or dev mode display).
"""
import hashlib
import sqlite3
import logging
from datetime import datetime, timedelta, timezone
from flask import render_template, request, redirect, url_for, flash, session, current_app, g
from app.db import get_db
from app.decorators import require_contest_context
from app.services.sms import validate_and_format_phone, send_verification_token, check_verification_token

logger = logging.getLogger(__name__)


def is_valid_email(email):
    """Basic email validation: must have @, at least one . after @, no spaces."""
    if not email or ' ' in email:
        return False
    if '@' not in email:
        return False
    local, _, domain = email.partition('@')
    if not local or not domain or '.' not in domain:
        return False
    return True


def register_routes(app):
    """Register authentication routes with Flask app."""

    @app.route('/<event_slug>/<contest_slug>/register', methods=['GET', 'POST'])
    @require_contest_context
    def register(event_slug, contest_slug):
        """
        Registration form and handler.
        User enters: name, email, phone, team_name
        → Create account + join contest → Set session → Immediately logged in (no OTP)
        """
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()  # Normalize to lowercase
            phone_input = request.form.get('phone', '').strip()
            team_name = request.form.get('team_name', '').strip()

            # Basic validation
            if not all([name, email, phone_input, team_name]):
                flash('All fields are required.', 'error')
                return render_template('auth/register.html',
                                     name=name, email=email, phone=phone_input, team_name=team_name)

            # Email format validation
            if not is_valid_email(email):
                flash('Invalid email address.', 'error')
                return render_template('auth/register.html',
                                     name=name, email=email, phone=phone_input, team_name=team_name)

            # Phone number validation and formatting
            valid, phone_number, error = validate_and_format_phone(phone_input)
            if not valid:
                flash(f'Invalid phone number: {error}', 'error')
                return render_template('auth/register.html',
                                     name=name, email=email, phone=phone_input, team_name=team_name)

            db = get_db()

            # Create user + join contest atomically
            try:
                db.execute('BEGIN')

                # Check if user already exists
                existing = db.execute('SELECT id, phone_number FROM users WHERE email = ?', [email]).fetchone()

                if existing:
                    # User exists - check if they need to complete registration (placeholder phone)
                    user_id = existing['id']
                    has_placeholder_phone = existing['phone_number'] == '+10000000000'

                    # If user has placeholder phone, update it (allows pre-seeded admins to complete setup)
                    if has_placeholder_phone:
                        db.execute('''
                            UPDATE users
                            SET phone_number = ?, name = ?, team_name = ?
                            WHERE id = ?
                        ''', [phone_number, name, team_name, user_id])
                        logger.info(f"Updated placeholder account for {email} with real phone number")

                    # Check if already in this contest
                    already_joined = db.execute('''
                        SELECT 1 FROM user_contest_info
                        WHERE user_id = ? AND contest_id = ?
                    ''', [user_id, g.contest['id']]).fetchone()

                    if already_joined and not has_placeholder_phone:
                        # Only show error if they're truly already registered (not completing setup)
                        db.rollback()
                        flash('You are already registered for this contest. Please log in.', 'error')
                        return redirect(url_for('login', event_slug=event_slug, contest_slug=contest_slug))

                    # Join contest (if not already joined)
                    if not already_joined:
                        db.execute('''
                            INSERT INTO user_contest_info (user_id, contest_id)
                            VALUES (?, ?)
                        ''', [user_id, g.contest['id']])

                else:
                    # Create new user
                    db.execute('''
                        INSERT INTO users (email, phone_number, name, team_name)
                        VALUES (?, ?, ?, ?)
                    ''', [email, phone_number, name, team_name])

                    # Get user_id
                    user_id = db.execute('SELECT id FROM users WHERE email = ?', [email]).fetchone()['id']

                    # Join contest
                    db.execute('''
                        INSERT INTO user_contest_info (user_id, contest_id)
                        VALUES (?, ?)
                    ''', [user_id, g.contest['id']])

                db.commit()

                # Log user in immediately (no OTP required for registration)
                session.permanent = True
                session['user_id'] = user_id

                flash('Registration successful! Welcome to the pool. You will stay logged in on this device.', 'success')
                return redirect(url_for('contest_home', event_slug=event_slug, contest_slug=contest_slug))

            except sqlite3.IntegrityError as e:
                db.rollback()
                logger.error(f"IntegrityError during registration: {e}")
                flash('Email already registered with different information. Please use a different email.', 'error')
                return render_template('auth/register.html',
                                     name=name, email=email, phone=phone_input, team_name=team_name)
            except sqlite3.Error as e:
                db.rollback()
                logger.error(f"Database error during registration: {e}")
                flash('Registration failed. Please try again.', 'error')
                return render_template('auth/register.html',
                                     name=name, email=email, phone=phone_input, team_name=team_name)

        return render_template('auth/register.html')

    @app.route('/<event_slug>/<contest_slug>/login', methods=['GET', 'POST'])
    @require_contest_context
    def login(event_slug, contest_slug):
        """
        Login form and handler.
        User enters: email OR phone
        → Check if session exists (same device) → if yes, redirect
        → If no session (new device), send OTP → redirect to /login/verify
        """
        if request.method == 'POST':
            identifier = request.form.get('identifier', '').strip()
            force_otp = request.form.get('force_otp') == '1'  # Dev/testing checkbox

            if not identifier:
                flash('Email or phone number is required.', 'error')
                return render_template('auth/login.html', identifier=identifier)

            # Try to parse as phone number first
            valid_phone, phone_number, _ = validate_and_format_phone(identifier)

            db = get_db()

            # Look up user by phone or email
            if valid_phone:
                user = db.execute('SELECT * FROM users WHERE phone_number = ?', [phone_number]).fetchone()
            else:
                # Try by email (normalize to lowercase for case-insensitive lookup)
                if not is_valid_email(identifier):
                    flash('Invalid email or phone number format.', 'error')
                    return render_template('auth/login.html', identifier=identifier)
                email_lower = identifier.lower()
                user = db.execute('SELECT * FROM users WHERE email = ?', [email_lower]).fetchone()

            if not user:
                flash('No account found. Please register first.', 'error')
                return render_template('auth/login.html', identifier=identifier)

            # Check if user already has valid session (same device)
            # Skip session check if force_otp is enabled (dev/testing)
            if not force_otp and str(session.get('user_id')) == str(user['id']):
                # Already logged in, just redirect to contest
                flash('Already logged in!', 'success')
                return redirect(url_for('contest_home', event_slug=event_slug, contest_slug=contest_slug))

            # New device login - send OTP
            # Rate limiting: max 3 OTPs per user per hour
            recent_otps = db.execute('''
                SELECT COUNT(*) as count FROM otp_codes
                WHERE user_id = ? AND created_at > datetime('now', 'utc', '-1 hour')
            ''', [user['id']]).fetchone()

            if recent_otps['count'] >= 3:
                flash('Too many verification attempts. Please try again in an hour.', 'error')
                return render_template('auth/login.html', identifier=identifier)

            # Send Verification (SMS or Local Generation)
            success, result = send_verification_token(user['phone_number'])

            if not success:
                flash(f'Failed to send verification code: {result}', 'error')
                return render_template('auth/login.html', identifier=identifier)

            # Store user_id, phone, and contest context in session temporarily for OTP verification
            session['otp_user_id'] = user['id']
            session['otp_phone'] = user['phone_number']
            session['otp_redirect_event'] = event_slug
            session['otp_redirect_contest'] = contest_slug

            # NO_SMS_MODE: Result is the OTP code. Store in DB and show on page.
            if current_app.config.get('NO_SMS_MODE'):
                otp_code = result
                otp_hash = hashlib.sha256(otp_code.encode()).hexdigest()
                expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()

                try:
                    db.execute('''
                        INSERT INTO otp_codes (user_id, code_hash, expires_at)
                        VALUES (?, ?, ?)
                    ''', [user['id'], otp_hash, expires_at])
                    db.commit()
                except sqlite3.Error as e:
                    logger.error(f"Failed to create OTP for user {user['id']}: {e}")
                    flash('Failed to generate verification code. Please try again.', 'error')
                    return render_template('auth/login.html', identifier=identifier)

                return render_template('auth/login_verify.html',
                                     phone=user['phone_number'],
                                     otp_code=otp_code)

            flash('Verification code sent! Check your phone.', 'info')
            return redirect(url_for('login_verify', event_slug=event_slug, contest_slug=contest_slug))

        return render_template('auth/login.html')

    @app.route('/<event_slug>/<contest_slug>/login/verify', methods=['GET', 'POST'])
    @require_contest_context
    def login_verify(event_slug, contest_slug):
        """OTP verification page (only for new device logins)."""
        user_id = session.get('otp_user_id')
        phone = session.get('otp_phone')

        if not user_id:
            flash('Session expired. Please log in again.', 'error')
            return redirect(url_for('login', event_slug=event_slug, contest_slug=contest_slug))

        if request.method == 'POST':
            entered_code = request.form.get('otp_code', '').strip()

            if not entered_code or len(entered_code) != 4:
                flash('Please enter the 4-digit code.', 'error')
                return render_template('auth/login_verify.html', phone=phone)

            # Verify OTP
            db = get_db()

            # Dev Mode: Check Local DB
            if current_app.config.get('NO_SMS_MODE'):
                code_hash = hashlib.sha256(entered_code.encode()).hexdigest()

                otp_record = db.execute('''
                    SELECT * FROM otp_codes
                    WHERE user_id = ?
                    AND code_hash = ?
                    AND used_at IS NULL
                    AND expires_at > datetime('now', 'utc')
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', [user_id, code_hash]).fetchone()

                if not otp_record:
                    flash('Invalid or expired code. Please try again.', 'error')
                    return render_template('auth/login_verify.html', phone=phone)

                # Mark OTP as used
                db.execute('UPDATE otp_codes SET used_at = ? WHERE id = ?',
                          [datetime.now(timezone.utc).isoformat(), otp_record['id']])
                db.commit()

            # Production Mode: Check Twilio Verify
            else:
                valid, msg = check_verification_token(phone, entered_code)
                if not valid:
                    flash(f'Verification failed: {msg}', 'error')
                    return render_template('auth/login_verify.html', phone=phone)

            # Get redirect context
            redirect_event = session.pop('otp_redirect_event', event_slug)
            redirect_contest = session.pop('otp_redirect_contest', contest_slug)

            # Clear temporary session data
            session.pop('otp_user_id', None)
            session.pop('otp_phone', None)

            # Set permanent session (remember this device)
            session.permanent = True
            session['user_id'] = user_id

            flash('Successfully logged in!', 'success')
            return redirect(url_for('contest_home', event_slug=redirect_event, contest_slug=redirect_contest))

        return render_template('auth/login_verify.html', phone=phone)

    @app.route('/logout')
    def logout():
        """Clear session and log out."""
        session.clear()
        flash('You have been logged out.', 'info')
        return redirect(url_for('contest_selector'))
