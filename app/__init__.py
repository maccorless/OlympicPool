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

    # Context processor to make user available in all templates
    @app.context_processor
    def inject_user():
        from app.decorators import get_current_user
        return {'user': get_current_user()}

    # Register all routes (imported here to avoid circular imports)
    from app.routes import auth, draft, leaderboard, admin
    auth.register_routes(app)
    draft.register_routes(app)
    leaderboard.register_routes(app)
    admin.register_routes(app)

    # Home route
    @app.route('/')
    def index():
        from flask import render_template
        from app.db import get_db

        db_conn = get_db()
        contest = db_conn.execute('SELECT state FROM contest WHERE id = 1').fetchone()

        return render_template('index.html', contest_state=contest['state'])

    # One-time database setup endpoint (remove after first use)
    @app.route('/setup-database-now')
    def setup_database():
        """Initialize database with new schema. Visit this URL once after deployment."""
        from flask import jsonify
        from app.db import init_db, load_countries

        try:
            init_db()
            load_countries()
            return jsonify({
                'status': 'success',
                'message': 'Database initialized successfully! You can now use the app.',
                'next_step': 'Visit / to register'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    return app
