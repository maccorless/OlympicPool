#!/bin/bash
# Import data by POSTing SQL to a temporary admin endpoint

set -e

echo "Data Import via HTTP Endpoint"
echo "=============================="
echo ""

LOCAL_DB="/Users/kcorless/Documents/Projects/OlympicPool2/instance/medal_pool.db"

if [ ! -f "$LOCAL_DB" ]; then
    echo "Error: Local database not found"
    exit 1
fi

echo "Step 1: Export data from local database..."

# Create SQL that clears and imports data
EXPORT_FILE="/tmp/import_data_$(date +%s).sql"

cat > "$EXPORT_FILE" << 'SQLHEADER'
-- Clear existing data
DELETE FROM picks;
DELETE FROM medals;
DELETE FROM user_contest_info;
DELETE FROM users;
DELETE FROM contest;
DELETE FROM countries;
DELETE FROM events;
DELETE FROM system_meta;
DELETE FROM otp_codes;

-- Reset sequences
DELETE FROM sqlite_sequence;

SQLHEADER

# Add data exports
sqlite3 "$LOCAL_DB" << 'EOF' >> "$EXPORT_FILE"
.mode insert events
SELECT * FROM events;
.mode insert contest
SELECT * FROM contest;
.mode insert users
SELECT * FROM users;
.mode insert countries
SELECT * FROM countries;
.mode insert user_contest_info
SELECT * FROM user_contest_info;
.mode insert picks
SELECT * FROM picks;
.mode insert medals
SELECT * FROM medals;
.mode insert system_meta
SELECT * FROM system_meta;
EOF

echo "✓ Data exported to SQL file"
echo ""

echo "Step 2: Import via HTTP POST to Railway..."
echo ""
echo "Sending data to https://medalpool.com/admin/import-data..."
echo ""

# POST the SQL to the endpoint (with import token)
IMPORT_TOKEN="${IMPORT_TOKEN:-temp-import-secret-12345}"
HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/import_response.txt -X POST \
  -H "Content-Type: application/sql" \
  -H "X-Import-Token: $IMPORT_TOKEN" \
  --data-binary @"$EXPORT_FILE" \
  "https://medalpool.com/admin/import-data")

BODY=$(cat /tmp/import_response.txt)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ Import successful!"
    echo ""
    echo "Response:"
    echo "$BODY"
else
    echo "✗ Import failed (HTTP $HTTP_CODE)"
    echo ""
    echo "Response:"
    echo "$BODY"
    echo ""
    echo "Note: The import endpoint may not exist yet."
    echo "You need to add it to app/routes/admin.py first."
    exit 1
fi

# Cleanup
rm -f "$EXPORT_FILE" /tmp/import_response.txt

echo ""
echo "Done! Visit https://medalpool.com to verify."
