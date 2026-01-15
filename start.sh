#!/bin/bash
set -e

echo "Starting Olympic Medal Pool..."

# Initialize database if it doesn't exist
if [ ! -f "instance/medal_pool.db" ]; then
    echo "Database not found. Initializing..."
    flask init-db
    echo "Database initialized successfully."
else
    echo "Database already exists."
fi

# Start gunicorn
echo "Starting gunicorn..."
exec gunicorn "app:create_app()"
