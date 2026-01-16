"""
Route decorators for authentication and authorization.
"""
from functools import wraps
from flask import session, redirect, url_for, abort, current_app, g, request
from app.db import get_db


def get_contest_from_url():
    """
    Extract contest and event from URL path.

    Expected URL pattern: /<event_slug>/<contest_slug>/...
    Returns: Dict with contest and event info, or None if not found.
    """
    # Return cached contest if already fetched this request
    if 'cached_contest' in g:
        return g.cached_contest

    # Parse URL path to extract slugs
    path_parts = request.path.strip('/').split('/')

    # Need at least 2 parts for event_slug/contest_slug
    if len(path_parts) < 2:
        g.cached_contest = None
        return None

    event_slug = path_parts[0]
    contest_slug = path_parts[1]

    # Look up contest + event
    db = get_db()
    result = db.execute('''
        SELECT
            c.id as contest_id,
            c.event_id,
            c.slug as contest_slug,
            c.name as contest_name,
            c.description as contest_description,
            c.state,
            c.budget,
            c.max_countries,
            c.deadline,
            e.id as event_id,
            e.name as event_name,
            e.slug as event_slug,
            e.description as event_description,
            e.start_date,
            e.end_date,
            e.is_active
        FROM contest c
        JOIN events e ON c.event_id = e.id
        WHERE e.slug = ? AND c.slug = ?
    ''', [event_slug, contest_slug]).fetchone()

    if not result:
        g.cached_contest = None
        return None

    # Split into contest and event dicts
    contest = {
        'id': result['contest_id'],
        'event_id': result['event_id'],
        'slug': result['contest_slug'],
        'name': result['contest_name'],
        'description': result['contest_description'],
        'state': result['state'],
        'budget': result['budget'],
        'max_countries': result['max_countries'],
        'deadline': result['deadline'],
        'event': {
            'id': result['event_id'],
            'name': result['event_name'],
            'slug': result['event_slug'],
            'description': result['event_description'],
            'start_date': result['start_date'],
            'end_date': result['end_date'],
            'is_active': result['is_active']
        }
    }

    # Cache for this request
    g.cached_contest = contest
    return contest


def require_contest_context(f):
    """
    Decorator to ensure valid contest context exists.
    Sets g.contest and g.event for use in route handlers.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        contest = get_contest_from_url()
        if not contest:
            abort(404, "Contest not found")

        # Make contest and event available in g
        g.contest = contest
        g.event = contest['event']

        return f(*args, **kwargs)
    return decorated_function


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
        if user['email'] not in current_app.config['ADMIN_EMAILS']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def require_state(*allowed_states):
    """
    Decorator to enforce contest state. Usage: @require_state('open')

    NOTE: This decorator requires contest context (use after @require_contest_context).
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Contest must be loaded in g.contest (by @require_contest_context)
            if not hasattr(g, 'contest') or not g.contest:
                abort(500, "Contest context not loaded")

            if g.contest['state'] not in allowed_states:
                abort(403, f"Action not allowed in '{g.contest['state']}' state")
            return f(*args, **kwargs)
        return decorated_function
    return decorator
