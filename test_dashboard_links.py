#!/usr/bin/env python3
"""
Extract and test all links from the global admin dashboard.
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import re
from app import create_app

def login_as_admin(client):
    """Login as admin using Flask test client."""
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

            if response.status_code == 200:
                return True

    return False

def extract_links(html):
    """Extract all href links from HTML."""
    # Find all href attributes
    links = re.findall(r'href="([^"]+)"', html)
    return links

def test_dashboard_links():
    """Extract and test all links from dashboard."""
    print("\n" + "="*70)
    print("TESTING LINKS IN GLOBAL ADMIN DASHBOARD")
    print("="*70)

    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    client = app.test_client()

    # Login as admin
    print("\n📝 Logging in...")
    if not login_as_admin(client):
        print("❌ Could not login")
        return False

    # Get dashboard
    response = client.get('/admin/global', follow_redirects=False)

    if response.status_code != 200:
        print(f"❌ Dashboard returned {response.status_code}")
        return False

    html = response.data.decode('utf-8')

    # Extract all links
    all_links = extract_links(html)

    # Filter for admin/global links
    admin_links = [link for link in all_links if '/admin/global' in link]

    print("\nLinks found in dashboard:")
    for link in sorted(set(admin_links)):
        print(f"  {link}")

    # Test each unique admin link
    print("\nTesting each link:")
    all_good = True
    tested_links = set()

    for link in admin_links:
        # Skip if already tested
        if link in tested_links:
            continue

        tested_links.add(link)

        # Skip form action links (they require POST)
        if '/delete' in link or '/create' in link or '/edit' in link:
            print(f"  ⏭️  {link:50s} (Skipped - form action)")
            continue

        # Test GET request
        response = client.get(link, follow_redirects=False)

        if response.status_code == 200:
            print(f"  ✅ {link:50s} (200 OK)")
        elif response.status_code in [301, 302]:
            print(f"  ⚠️  {link:50s} (Redirect to {response.location})")
        elif response.status_code == 401:
            print(f"  ❌ {link:50s} (401 Unauthorized)")
            all_good = False
        elif response.status_code == 403:
            print(f"  ❌ {link:50s} (403 Forbidden)")
            all_good = False
        elif response.status_code == 404:
            print(f"  ❌ {link:50s} (404 Not Found)")
            all_good = False
        else:
            print(f"  ❌ {link:50s} ({response.status_code})")
            all_good = False

    print("\n" + "="*70)
    if all_good:
        print("✅ ALL LINKS WORK CORRECTLY")
    else:
        print("❌ SOME LINKS HAVE ISSUES")
    print("="*70)

    return all_good

if __name__ == '__main__':
    success = test_dashboard_links()
    exit(0 if success else 1)
