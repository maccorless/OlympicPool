#!/usr/bin/env python3
"""
Test if Global Admin link is visible in navigation after login.
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import re
from app import create_app

def login_as_admin(client):
    """Login as admin."""
    response = client.post('/corless26/default/login',
                          data={'identifier': 'ken@corless.com'},
                          follow_redirects=False)

    if response.status_code == 200:
        html = response.data.decode('utf-8')
        otp_match = re.search(r'<p class="text-4xl font-mono font-bold text-center text-yellow-900">(\d{4})</p>', html)

        if otp_match:
            otp_code = otp_match.group(1)
            response = client.post('/corless26/default/login/verify',
                                  data={'otp_code': otp_code},
                                  follow_redirects=True)
            return response.status_code == 200

    return False

def test_global_admin_link():
    """Test if Global Admin link appears after login."""
    print("\n" + "="*70)
    print("TESTING GLOBAL ADMIN LINK VISIBILITY")
    print("="*70)

    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    client = app.test_client()

    print("\n1️⃣  Before Login - Check Homepage")
    print("-" * 70)
    response = client.get('/', follow_redirects=False)
    html = response.data.decode('utf-8')

    if '🌐 Global Admin' in html or 'global_admin_dashboard' in html:
        print("⚠️  Global Admin link visible BEFORE login (shouldn't be)")
    else:
        print("✅ Global Admin link NOT visible (correct)")

    print("\n2️⃣  Logging In")
    print("-" * 70)
    if not login_as_admin(client):
        print("❌ Could not login")
        return False
    print("✅ Login successful")

    print("\n3️⃣  After Login - Check Contest Homepage")
    print("-" * 70)
    response = client.get('/corless26/default', follow_redirects=False)
    html = response.data.decode('utf-8')

    # Save HTML for inspection
    with open('/tmp/logged_in_page.html', 'w') as f:
        f.write(html)

    # Check for Global Admin link
    if '🌐 Global Admin' in html:
        print("✅ Global Admin link IS visible (with emoji)")
    elif 'Global Admin' in html:
        print("✅ Global Admin link IS visible (without emoji)")
    elif '/admin/global' in html:
        print("✅ Global Admin URL found in page")
    else:
        print("❌ Global Admin link NOT visible")
        print("   (HTML saved to /tmp/logged_in_page.html for debugging)")

        # Check if condition variables are present
        print("\n   Debugging - Checking template conditions:")
        if 'session.user_id' in html or 'user_id' in html:
            print("   ⚠️  session.user_id might be set")
        if 'ken@corless.com' in html:
            print("   ✅ User email found in page")

    print("\n4️⃣  Direct Access to Global Admin")
    print("-" * 70)
    response = client.get('/admin/global', follow_redirects=False)

    if response.status_code == 200:
        print("✅ Can access /admin/global directly (200 OK)")
    elif response.status_code == 401:
        print("❌ Cannot access /admin/global (401 Unauthorized)")
        return False
    elif response.status_code == 403:
        print("❌ Cannot access /admin/global (403 Forbidden)")
        return False
    else:
        print(f"⚠️  Unexpected status: {response.status_code}")

    print("\n" + "="*70)
    print("✅ TEST COMPLETE")
    print("="*70)

    return True

if __name__ == '__main__':
    success = test_global_admin_link()
    exit(0 if success else 1)
