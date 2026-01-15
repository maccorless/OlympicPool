#!/bin/bash
set -e

echo "Starting Olympic Medal Pool..."

# Ensure database directory exists (for Railway volumes)
DB_DIR="${DATABASE_DIR:-instance}"
mkdir -p "$DB_DIR"
echo "Database directory: $DB_DIR"

DB_PATH="$DB_DIR/medal_pool.db"

# Initialize database if it doesn't exist
if [ ! -f "$DB_PATH" ]; then
    echo "Database not found at $DB_PATH. Initializing..."
    flask init-db
    echo "Database initialized."
else
    echo "Database already exists at $DB_PATH"
fi

# Load countries (only loads if table is empty - safe to run every time)
flask load-countries

# Start gunicorn
echo "Starting gunicorn..."
exec gunicorn "app:create_app()"
