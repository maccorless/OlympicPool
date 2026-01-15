#!/bin/bash
set -e

echo "Starting Olympic Medal Pool..."

# Initialize database if it doesn't exist
if [ ! -f "instance/medal_pool.db" ]; then
    echo "Database not found. Initializing..."
    flask init-db
    echo "Database initialized successfully."
fi

# Check if countries are loaded
COUNTRY_COUNT=$(sqlite3 instance/medal_pool.db "SELECT COUNT(*) FROM countries;" 2>/dev/null || echo "0")
if [ "$COUNTRY_COUNT" -eq "0" ]; then
    echo "Countries table is empty. Loading countries data..."
    sqlite3 instance/medal_pool.db < data/countries.sql
    echo "Countries loaded successfully. Total: $(sqlite3 instance/medal_pool.db "SELECT COUNT(*) FROM countries;")"
else
    echo "Countries already loaded. Total: $COUNTRY_COUNT"
fi

# Start gunicorn
echo "Starting gunicorn..."
exec gunicorn "app:create_app()"
