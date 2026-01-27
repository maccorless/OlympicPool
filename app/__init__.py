"""
Flask app factory - Olympic Medal Pool
Simple, flat route registration without blueprints.
"""
import os
from flask import Flask

# CRITICAL: Load .env BEFORE importing any app modules that use config
import os as _os
try:
    from dotenv import load_dotenv, find_dotenv

    # Find .env file explicitly
    dotenv_path = find_dotenv()
    if dotenv_path:
        print(f"🔍 Loading .env from: {dotenv_path}")
        load_dotenv(dotenv_path, override=True)
        print(f"   NO_EMAIL_MODE after load_dotenv: {_os.getenv('NO_EMAIL_MODE')}")
    else:
        # Only warn if not running on Railway (Railway uses env vars directly)
        if not _os.getenv('RAILWAY_ENVIRONMENT'):
            print("⚠️  WARNING: No .env file found!")

except ImportError:
    print("⚠️  WARNING: python-dotenv not installed")
    pass  # python-dotenv not installed, will use environment variables


def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration
    if test_config is None:
        app.config.from_object('app.config')
    else:
        app.config.from_mapping(test_config)
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize database
    from app import db
    db.init_app(app)

    # Add security headers
    @app.after_request
    def add_security_headers(response):
        """Add Content Security Policy and other security headers."""
        # CSP allows Alpine.js (requires unsafe-eval) and our CDN resources
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "https://cdn.tailwindcss.com https://unpkg.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
            "img-src 'self' data: https://flagcdn.com; "
            "connect-src 'self'; "
            "font-src 'self' data:; "
            "frame-ancestors 'none'; "
            "base-uri 'self';"
        )
        response.headers['Content-Security-Policy'] = csp_policy

        # Additional security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'

        return response

    # Context processor to make user and config available in all templates
    @app.context_processor
    def inject_user():
        from app.decorators import get_current_user
        from flask import g, current_app

        context = {
            'user': get_current_user(),
            'config': current_app.config  # Make config available in templates
        }

        # Inject contest and event if available
        if hasattr(g, 'contest') and g.contest:
            context['contest'] = g.contest
            context['event'] = g.event

        return context

    # Register all routes (imported here to avoid circular imports)
    from app.routes import events, auth, draft, leaderboard, admin, global_admin
    events.register_routes(app)  # FIRST - defines /
    auth.register_routes(app)
    draft.register_routes(app)
    leaderboard.register_routes(app)
    admin.register_routes(app)
    global_admin.register_routes(app)  # Global admin routes (no contest context required)

    return app
