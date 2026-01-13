"""
Flask app factory - Olympic Medal Pool
Simple, flat route registration without blueprints.
"""
import os
from flask import Flask


def create_app(test_config=None):
    """Create and configure the Flask application."""
    # Load .env file (optional - falls back to environment variables)
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # python-dotenv not installed, will use environment variables

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

    return app
