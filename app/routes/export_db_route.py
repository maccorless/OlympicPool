"""
Database export route for Railway deployment.
Access via: /admin/export-database
"""
import os
import sqlite3
from flask import Response, abort
from app.decorators import admin_required

def register_routes(app):
    """Register database export route."""

    @app.route('/admin/export-database', methods=['GET'])
    @admin_required
    def export_database():
        """Export database as SQL dump (Railway only)."""

        # Get database path
        db_dir = os.getenv('DATABASE_DIR', '/app/instance')
        db_path = os.path.join(db_dir, 'medal_pool.db')

        # Safety check - only allow on Railway
        if not os.getenv('RAILWAY_ENVIRONMENT'):
            abort(403, "This endpoint only works on Railway")

        if not os.path.exists(db_path):
            abort(404, f"Database not found at {db_path}")

        # Generate SQL dump
        conn = sqlite3.connect(db_path)
        sql_dump = '\n'.join(conn.iterdump())
        conn.close()

        # Return as downloadable file
        return Response(
            sql_dump,
            mimetype='text/plain',
            headers={
                'Content-Disposition': 'attachment; filename=production_export.sql'
            }
        )

    @app.route('/admin/database-info', methods=['GET'])
    @admin_required
    def database_info():
        """Show database location and stats."""
        from flask import jsonify

        db_dir = os.getenv('DATABASE_DIR', '/app/instance')
        db_path = os.path.join(db_dir, 'medal_pool.db')

        if not os.path.exists(db_path):
            return jsonify({
                'error': f'Database not found at {db_path}',
                'db_dir': db_dir,
                'exists': False
            })

        # Get stats
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM picks")
        pick_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM countries")
        country_count = cursor.fetchone()[0]

        conn.close()

        return jsonify({
            'db_path': db_path,
            'db_dir': db_dir,
            'exists': True,
            'users': user_count,
            'picks': pick_count,
            'countries': country_count
        })
