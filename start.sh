#!/bin/bash
set -e

echo "Starting Olympic Medal Pool..."

# Initialize database if it doesn't exist
if [ ! -f "instance/medal_pool.db" ]; then
    echo "Database not found. Initializing..."
    flask init-db
fi

# Load countries (only loads if table is empty - safe to run every time)
flask load-countries

# Start gunicorn
echo "Starting gunicorn..."
exec gunicorn "app:create_app()"
