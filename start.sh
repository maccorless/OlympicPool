#!/bin/bash
set -e

echo "Starting Olympic Medal Pool..."

# Initialize database if it doesn't exist
if [ ! -f "instance/medal_pool.db" ]; then
    echo "Database not found. Initializing..."
    flask init-db
    echo "Database initialized successfully."

    # Load countries data
    echo "Loading countries data..."
    sqlite3 instance/medal_pool.db < data/countries.sql
    echo "Countries loaded successfully."
else
    echo "Database already exists."
fi

# Start gunicorn
echo "Starting gunicorn..."
exec gunicorn "app:create_app()"
