#!/usr/bin/env python3
"""
Test script for magic-link authentication (Step 2).
"""
import sys
import sqlite3
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test with a temp database
import tempfile
import os

db_path = tempfile.mktemp(suffix='.db')

try:
    # Create test app
    from app import create_app

    app = create_app({
        'DATABASE': db_path,
        'SECRET_KEY': 'test-key',
        'BASE_URL': 'http://localhost:5001',
        'ADMIN_EMAILS': ['admin@test.com'],
        'TESTING': True
    })

    with app.app_context():
        # Initialize database
        from app.db import init_db
        init_db()

        print("[test_auth] ✓ Database initialized")

        # Test registration
        with app.test_client() as client:
            response = client.post('/register', data={
                'name': 'Test User',
                'email': 'test@example.com',
                'team_name': 'Test Team'
            }, follow_redirects=False)

            assert response.status_code == 302, f"Expected 302, got {response.status_code}"
            assert response.location == '/check-email', f"Expected redirect to /check-email, got {response.location}"
            print("[test_auth] ✓ Registration redirects correctly")

            # Check user created
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            user = conn.execute('SELECT * FROM users WHERE email = ?', ['test@example.com']).fetchone()
            assert user is not None, "User not created"
            assert user['name'] == 'Test User'
            assert user['team_name'] == 'Test Team'
            print("[test_auth] ✓ User created in database")

            # Check token created
            token = conn.execute('SELECT * FROM tokens WHERE user_id = ?', [user['id']]).fetchone()
            assert token is not None, "Token not created"
            assert token['token_hash'] is not None
            assert token['used_at'] is None
            print("[test_auth] ✓ Magic link token created")

            # Test login (existing user)
            response = client.post('/login', data={
                'email': 'test@example.com'
            }, follow_redirects=False)

            assert response.status_code == 302
            print("[test_auth] ✓ Login sends magic link")

            # Check second token created
            tokens = conn.execute('SELECT * FROM tokens WHERE user_id = ?', [user['id']]).fetchall()
            assert len(tokens) == 2, f"Expected 2 tokens, got {len(tokens)}"
            print("[test_auth] ✓ Second token created for login")

            # Test login with non-existent user
            response = client.post('/login', data={
                'email': 'nonexistent@example.com'
            }, follow_redirects=False)

            assert response.status_code == 200, "Should show error on same page"
            print("[test_auth] ✓ Login rejects non-existent user")

            # Test /check-email page
            response = client.get('/check-email')
            assert response.status_code == 200
            assert b'Check Your Email' in response.data
            print("[test_auth] ✓ Check email page renders")

            # Test logout
            response = client.get('/logout', follow_redirects=False)
            assert response.status_code == 302
            assert response.location == '/'
            print("[test_auth] ✓ Logout redirects to home")

            conn.close()

    print("[test_auth] ✅ All authentication tests passed!")

finally:
    if os.path.exists(db_path):
        os.unlink(db_path)
        print("[test_auth] Cleaned up test database")
