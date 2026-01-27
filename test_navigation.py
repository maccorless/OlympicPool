#!/usr/bin/env python3
"""
Test navigation through all global admin links.
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import re
from app import create_app

def login_as_admin(client):
    """Login as admin using Flask test client."""
    # Step 1: POST to login (use correct event slug from database)
    response = client.post('/corless26/default/login',
                          data={'identifier': 'ken@corless.com'},
                          follow_redirects=False)

    print(f"  Login POST status: {response.status_code}")

    if response.status_code == 200:
        html = response.data.decode('utf-8')

        # Save HTML for debugging
        with open('/tmp/login_response.html', 'w') as f:
            f.write(html)

        # Look for OTP in HTML
        otp_match = re.search(r'<p class="text-4xl font-mono font-bold text-center text-yellow-900">(\d{4})</p>', html)

        if otp_match:
            otp_code = otp_match.group(1)
            print(f"  Extracted OTP: {otp_code}")

            # Step 2: POST to verify OTP
            response = client.post('/corless26/default/login/verify',
                                  data={'otp_code': otp_code},
                                  follow_redirects=True)

            print(f"  OTP verify status: {response.status_code}")

            if response.status_code == 200:
                return True
        else:
            print("  Could not find OTP in response")
            print("  HTML saved to /tmp/login_response.html for debugging")
    else:
        print(f"  Unexpected response status: {response.status_code}")

    return False

def test_navigation():
    """Test all navigation paths in global admin."""
    print("\n" + "="*70)
    print("TESTING GLOBAL ADMIN NAVIGATION")
    print("="*70)

    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    client = app.test_client()

    # Login as admin
    print("\n📝 Logging in as admin...")
    if not login_as_admin(client):
        print("❌ Could not login")
        return False

    print("✅ Login successful\n")

    # Test navigation paths
    paths_to_test = [
        ('GET', '/admin/global', 'Global Admin Dashboard'),
        ('GET', '/admin/global/events', 'Manage Events'),
        ('GET', '/admin/global/events/create', 'Create Event Form'),
        ('GET', '/admin/global/contests', 'Manage Contests'),
        ('GET', '/admin/global/contests/create', 'Create Contest Form'),
    ]

    all_good = True

    for method, path, description in paths_to_test:
        response = client.get(path, follow_redirects=False)

        if response.status_code == 200:
            print(f"✅ {description:30s} → {path}")
        elif response.status_code == 302:
            print(f"⚠️  {description:30s} → {path} (Redirect to {response.location})")
            all_good = False
        elif response.status_code == 401:
            print(f"❌ {description:30s} → {path} (401 Unauthorized)")
            all_good = False
        elif response.status_code == 403:
            print(f"❌ {description:30s} → {path} (403 Forbidden)")
            all_good = False
        elif response.status_code == 404:
            print(f"❌ {description:30s} → {path} (404 Not Found)")
            all_good = False
        else:
            print(f"❌ {description:30s} → {path} (Status: {response.status_code})")
            all_good = False

    # Test link extraction from dashboard
    print("\n" + "="*70)
    print("TESTING LINKS IN DASHBOARD PAGE")
    print("="*70)

    response = client.get('/admin/global', follow_redirects=False)
    if response.status_code == 200:
        html = response.data.decode('utf-8')

        # Check for specific links
        expected_links = [
            'global_admin_event_create',
            'global_admin_contest_create',
            'global_admin_events',
            'global_admin_contests',
        ]

        for link_name in expected_links:
            if link_name in html:
                print(f"✅ Found link: {link_name}")
            else:
                print(f"❌ Missing link: {link_name}")
                all_good = False

    print("\n" + "="*70)
    if all_good:
        print("✅ ALL NAVIGATION WORKS CORRECTLY")
    else:
        print("❌ SOME NAVIGATION ISSUES FOUND")
    print("="*70)

    return all_good

if __name__ == '__main__':
    success = test_navigation()
    exit(0 if success else 1)
