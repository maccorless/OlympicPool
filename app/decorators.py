"""
Route decorators for authentication and authorization.
"""
from functools import wraps
from flask import session, redirect, url_for, abort, current_app, g
from app.db import get_db


def get_current_user():
    """
    Get current user from session, cached in g for request lifetime.

    This function caches the user in Flask's g object to avoid redundant
    database queries within a single request. The cache is automatically
    cleared at the end of each request.
    """
    # Return cached user if we already fetched it this request
    if 'cached_user' in g:
        return g.cached_user

    user_id = session.get('user_id')
    if not user_id:
        g.cached_user = None
        return None

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', [user_id]).fetchone()

    # Cache for this request
    g.cached_user = user
    return user


def login_required(f):
    """Decorator to require logged-in user."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not get_current_user():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin user (based on ADMIN_EMAILS config)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            abort(401)
        # Case-insensitive email comparison (both normalized to lowercase)
        if user['email'].lower() not in current_app.config['ADMIN_EMAILS']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def require_state(*allowed_states):
    """Decorator to enforce contest state. Usage: @require_state('open')"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            db = get_db()
            contest = db.execute('SELECT state FROM contest WHERE id = 1').fetchone()
            if contest['state'] not in allowed_states:
                abort(403, f"Action not allowed in '{contest['state']}' state")
            return f(*args, **kwargs)
        return decorated_function
    return decorator
