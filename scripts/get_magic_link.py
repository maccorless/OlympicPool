#!/usr/bin/env python3
"""
Development helper: Generate a magic link for a user.
Usage: python scripts/get_magic_link.py <email>
"""
import sys
import sqlite3
import secrets
import hashlib
from datetime import datetime, timedelta, timezone

if len(sys.argv) < 2:
    print("Usage: python scripts/get_magic_link.py <email>")
    print("Example: python scripts/get_magic_link.py test@example.com")
    sys.exit(1)

email = sys.argv[1]
db_path = 'instance/medal_pool.db'

# Connect to database
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# Get user
user = conn.execute('SELECT id, name FROM users WHERE email = ?', [email]).fetchone()

if not user:
    print(f"ERROR: No user found with email {email}")
    print("Register first with:")
    print(f"  curl -X POST http://localhost:5001/register -d 'name=Test&email={email}&team_name=Team'")
    sys.exit(1)

# Generate token
token = secrets.token_urlsafe(32)
token_hash = hashlib.sha256(token.encode()).hexdigest()
expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

# Store token
conn.execute('INSERT INTO tokens (token_hash, user_id, expires_at) VALUES (?, ?, ?)',
             [token_hash, user['id'], expires_at])
conn.commit()
conn.close()

print(f"\n{'='*60}")
print(f"Magic link for {email} ({user['name']}):")
print(f"http://localhost:5001/auth/{token}")
print(f"\nVisit in browser or curl:")
print(f"  curl -L http://localhost:5001/auth/{token}")
print(f"{'='*60}\n")
