"""
Migration endpoint for Railway deployment.
Access via: /admin/run-migration
"""
import os
import sqlite3
from flask import jsonify, abort
from app.decorators import admin_required

def register_routes(app):
    """Register migration route."""

    @app.route('/admin/run-migration', methods=['POST'])
    @admin_required
    def run_migration():
        """Run migration to add wikipedia_medal_url column."""

        # Get database path
        db_dir = os.getenv('DATABASE_DIR', '/app/instance')
        db_path = os.path.join(db_dir, 'medal_pool.db')

        # Safety check - only allow on Railway
        if not os.getenv('RAILWAY_ENVIRONMENT'):
            abort(403, "This endpoint only works on Railway")

        if not os.path.exists(db_path):
            return jsonify({
                'success': False,
                'error': f'Database not found at {db_path}'
            }), 404

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            # Check if column already exists
            cursor.execute("PRAGMA table_info(contest)")
            columns = [row[1] for row in cursor.fetchall()]

            if 'wikipedia_medal_url' in columns:
                conn.close()
                return jsonify({
                    'success': True,
                    'message': 'Column already exists, no migration needed',
                    'already_existed': True
                })

            # Add the column
            cursor.execute("ALTER TABLE contest ADD COLUMN wikipedia_medal_url TEXT")

            # Set default URL
            cursor.execute("""
                UPDATE contest
                SET wikipedia_medal_url = 'https://en.wikipedia.org/wiki/2026_Winter_Olympics_medal_table'
                WHERE id = 1
            """)

            conn.commit()
            conn.close()

            return jsonify({
                'success': True,
                'message': 'Migration completed successfully',
                'wikipedia_url': 'https://en.wikipedia.org/wiki/2026_Winter_Olympics_medal_table',
                'already_existed': False
            })

        except Exception as e:
            conn.rollback()
            conn.close()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
