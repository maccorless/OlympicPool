"""
Authentication routes: register, login, magic link verification, logout.
Email sending logic is inline (no service layer).
"""
import secrets
import hashlib
import sqlite3
import logging
from datetime import datetime, timedelta, timezone
from flask import render_template, request, redirect, url_for, flash, session, current_app
from app.db import get_db

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

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """Registration form and handler."""
        if request.method == 'POST':
            email = request.form.get('email', '').strip()
            name = request.form.get('name', '').strip()
            team_name = request.form.get('team_name', '').strip()

            # Basic validation
            if not email or not name or not team_name:
                flash('All fields are required.', 'error')
                return render_template('auth/register.html',
                                     email=email, name=name, team_name=team_name)

            # Email format validation
            if not is_valid_email(email):
                flash('Invalid email address.', 'error')
                return render_template('auth/register.html',
                                     email=email, name=name, team_name=team_name)

            db = get_db()

            # Check if user exists
            existing = db.execute('SELECT id FROM users WHERE email = ?', [email]).fetchone()

            if not existing:
                # Create new user + token atomically (transaction)
                try:
                    db.execute('BEGIN')
                    db.execute(
                        'INSERT INTO users (email, name, team_name) VALUES (?, ?, ?)',
                        [email, name, team_name]
                    )
                    # Create token within same transaction
                    user_id = db.execute('SELECT id FROM users WHERE email = ?', [email]).fetchone()['id']
                    success, error_msg = create_magic_link_token(db, user_id)
                    if not success:
                        db.rollback()
                        flash(error_msg, 'error')
                        return render_template('auth/register.html',
                                             email=email, name=name, team_name=team_name)
                    db.commit()
                except sqlite3.IntegrityError:
                    # Race condition: another request created this user
                    db.rollback()
                    logger.warning(f"Race condition on user creation for {email}")
                    # User exists now, fall through to send magic link
                except sqlite3.Error as e:
                    db.rollback()
                    logger.error(f"Database error during registration for {email}: {e}")
                    flash("Registration failed. Please try again.", 'error')
                    return render_template('auth/register.html',
                                         email=email, name=name, team_name=team_name)
            else:
                # Existing user - just create token
                success, error_msg = create_magic_link_token(db, existing['id'])
                if not success:
                    flash(error_msg, 'error')
                    return render_template('auth/register.html',
                                         email=email, name=name, team_name=team_name)
                db.commit()

            return redirect(url_for('check_email'))

        return render_template('auth/register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Login form and handler (request magic link)."""
        if request.method == 'POST':
            email = request.form.get('email', '').strip()

            if not email:
                flash('Email is required.', 'error')
                return render_template('auth/login.html', email=email)

            # Email format validation
            if not is_valid_email(email):
                flash('Invalid email address.', 'error')
                return render_template('auth/login.html', email=email)

            db = get_db()

            # Check if user exists
            user = db.execute('SELECT id FROM users WHERE email = ?', [email]).fetchone()

            if not user:
                # Don't reveal account existence (prevent enumeration)
                # Still show success message to avoid leaking information
                flash('If an account exists with that email, we\'ve sent you a login link.', 'info')
                return redirect(url_for('check_email'))

            # Create magic link token
            success, error_msg = create_magic_link_token(db, user['id'])

            if not success:
                # Generic error to avoid enumeration
                flash('Unable to send login link. Please try again.', 'error')
                return render_template('auth/login.html', email=email)

            db.commit()
            flash('Check your email for a login link.', 'info')
            return redirect(url_for('check_email'))

        return render_template('auth/login.html')

    @app.route('/check-email')
    def check_email():
        """Confirmation page after requesting magic link."""
        return render_template('auth/check_email.html')

    @app.route('/auth/<token>')
    def verify_magic_link(token):
        """Consume magic link token and log user in."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        db = get_db()

        # Find valid token
        token_row = db.execute('''
            SELECT * FROM tokens
            WHERE token_hash = ?
            AND used_at IS NULL AND expires_at > ?
        ''', [token_hash, datetime.now(timezone.utc).isoformat()]).fetchone()

        if not token_row:
            flash('This link has expired or already been used.', 'error')
            return redirect(url_for('login'))

        # Mark token as used
        db.execute('UPDATE tokens SET used_at = ? WHERE token_hash = ?',
                   [datetime.now(timezone.utc).isoformat(), token_hash])

        # Get user
        user = db.execute('SELECT * FROM users WHERE id = ?', [token_row['user_id']]).fetchone()

        if not user:
            flash('User not found.', 'error')
            db.commit()
            return redirect(url_for('login'))

        # Set session
        session.permanent = True
        session['user_id'] = user['id']

        # Clear any stored magic_link from session
        session.pop('magic_link', None)

        db.commit()

        flash('Successfully logged in!', 'success')
        return redirect(url_for('index'))

    @app.route('/logout')
    def logout():
        """Clear session and log out."""
        session.clear()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))


def create_magic_link_token(db, user_id):
    """
    Create magic link token for user and handle email/display.
    Does NOT commit - caller must commit.
    Returns (success: bool, error_message: str or None)
    """
    # Get user info
    user = db.execute('SELECT email, name FROM users WHERE id = ?', [user_id]).fetchone()
    if not user:
        return False, "User not found."

    # Rate limiting: max 3 tokens per user per hour
    # Use SQLite's datetime function for consistent timestamp comparison
    recent_tokens = db.execute('''
        SELECT COUNT(*) as count FROM tokens
        WHERE user_id = ? AND created_at > datetime('now', '-1 hour')
    ''', [user_id]).fetchone()

    if recent_tokens['count'] >= 3:
        return False, "Too many login attempts. Please try again in an hour."

    # Generate token
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    # Store token hash (without commit)
    try:
        db.execute('''
            INSERT INTO tokens (token_hash, user_id, expires_at)
            VALUES (?, ?, ?)
        ''', [token_hash, user_id, expires_at.isoformat()])
    except sqlite3.Error as e:
        logger.error(f"Failed to create token for user {user_id}: {e}")
        return False, "Failed to create login link. Please try again."

    # Build magic link URL using url_for
    magic_link = url_for('verify_magic_link', token=token, _external=True)

    # NO_EMAIL_MODE: store link in session to show on page
    if current_app.config.get('NO_EMAIL_MODE'):
        session['magic_link'] = magic_link
        logger.info(f"NO_EMAIL_MODE: Magic link for {user['email']}: {magic_link}")
        return True, None

    # Production: send email via Resend
    if current_app.config.get('RESEND_API_KEY'):
        try:
            import resend
            resend.api_key = current_app.config['RESEND_API_KEY']

            html = render_template('email/magic_link.html',
                                   name=user['name'],
                                   magic_link=magic_link)

            resend.Emails.send({
                "from": current_app.config['FROM_EMAIL'],
                "to": user['email'],
                "subject": "Your Olympic Medal Pool Login Link",
                "html": html
            })
            logger.info(f"Magic link email sent to {user['email']}")
            return True, None
        except Exception as e:
            logger.error(f"Failed to send email via Resend to {user['email']}: {e}")
            # Fall through to console fallback

    # Fallback: print to console (dev mode or Resend failure)
    logger.warning(f"Email not sent (Resend unavailable). Magic link for {user['email']}: {magic_link}")
    print(f"\n{'='*60}")
    print(f"MAGIC LINK FOR: {user['email']}")
    print(f"{'='*60}")
    print(magic_link)
    print(f"{'='*60}\n")

    # Store in session for display in fallback mode
    session['magic_link'] = magic_link

    return True, None
