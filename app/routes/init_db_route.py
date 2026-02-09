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

        # Check if database already has data and clear it
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                if user_count > 0:
                    # Clear all data before importing
                    cursor.execute("DELETE FROM picks")
                    cursor.execute("DELETE FROM otp_codes")
                    cursor.execute("DELETE FROM users")
                    cursor.execute("DELETE FROM medals")
                    cursor.execute("DELETE FROM system_meta")
                    cursor.execute("DELETE FROM contest")
                    cursor.execute("DELETE FROM countries")
                    conn.commit()
                    print(f"Cleared existing {user_count} users and all related data")
            except Exception as e:
                print(f"Could not clear existing data: {e}")
                pass
            conn.close()

        # Read production dump
        dump_file = os.path.join(app.root_path, '..', 'production_dump.sql')
        if not os.path.exists(dump_file):
            return jsonify({
                'success': False,
                'error': f'production_dump.sql not found at {dump_file}'
            }), 500

        with open(dump_file, 'r') as f:
            sql_dump = f.read()

        # Import into database
        conn = sqlite3.connect(db_path)
        try:
            conn.executescript(sql_dump)
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
