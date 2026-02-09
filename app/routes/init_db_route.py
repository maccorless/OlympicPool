"""
Database initialization route for Railway deployment.
Access via: /admin/init-database
"""
import os
import sqlite3
from flask import jsonify, abort
from app.decorators import admin_required

def register_routes(app):
    """Register database initialization route."""

    @app.route('/admin/init-database', methods=['POST'])
    @admin_required
    def init_database():
        """Initialize database from production dump (Railway only)."""

        # Get database path
        db_dir = os.getenv('DATABASE_DIR', '/app/instance')
        db_path = os.path.join(db_dir, 'medal_pool.db')

        # Safety check - only allow on Railway
        if not os.getenv('RAILWAY_ENVIRONMENT'):
            abort(403, "This endpoint only works on Railway")

        # Ensure directory exists
        os.makedirs(db_dir, exist_ok=True)

        # Drop all existing tables to allow fresh import
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get list of all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            # Drop all tables
            for table in tables:
                if table != 'sqlite_sequence':  # Keep sqlite internal table
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")

            # Drop indexes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in cursor.fetchall()]
            for index in indexes:
                if not index.startswith('sqlite_'):  # Keep sqlite internal indexes
                    cursor.execute(f"DROP INDEX IF EXISTS {index}")

            conn.commit()
            conn.close()
            print(f"Dropped all existing tables and indexes")

        # Read production dump
        dump_file = os.path.join(app.root_path, '..', 'production_dump.sql')
        if not os.path.exists(dump_file):
            return jsonify({
                'success': False,
                'error': f'production_dump.sql not found at {dump_file}'
            }), 500

        with open(dump_file, 'r') as f:
            sql_dump = f.read()

        # Import into database (as a transaction - all or nothing)
        conn = sqlite3.connect(db_path)
        try:
            # Execute SQL dump
            conn.executescript(sql_dump)

            # Verify tables were created
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            if 'contest' not in tables or 'users' not in tables:
                raise Exception("Import failed - required tables not created")

            conn.commit()

            # Verify
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM picks")
            pick_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM countries")
            country_count = cursor.fetchone()[0]

            conn.close()

            return jsonify({
                'success': True,
                'message': 'Database initialized successfully',
                'users': user_count,
                'picks': pick_count,
                'countries': country_count
            })

        except Exception as e:
            conn.rollback()
            conn.close()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
