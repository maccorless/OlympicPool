#!/usr/bin/env python3
"""
Test global admin functionality.
"""
import sqlite3
import requests
import re

BASE_URL = "http://127.0.0.1:5002"
DB_PATH = "instance/medal_pool.db"

def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def login_as_admin(session):
    """Login as admin user."""
    # Make sure admin has real phone
    db = get_db()
    admin = db.execute('SELECT * FROM users WHERE email = ?', ['ken@corless.com']).fetchone()

    if admin['phone_number'] == '+10000000000':
        # Complete registration first
        session.post(f"{BASE_URL}/milano-2026/default/register", data={
            'name': 'Ken Corless',
            'email': 'ken@corless.com',
            'phone': '+12065559999',
            'team_name': 'Admin Team'
        })

    db.close()

    # Login
    response = session.post(
        f"{BASE_URL}/milano-2026/default/login",
        data={'identifier': 'ken@corless.com'},
        allow_redirects=True
    )

    # Extract and submit OTP
    otp_match = re.search(r'<p class="text-4xl font-mono font-bold text-center text-yellow-900">(\d{4})</p>', response.text)
    if otp_match:
        otp_code = otp_match.group(1)
        session.post(
            f"{BASE_URL}/milano-2026/default/login/verify",
            data={'otp_code': otp_code},
            allow_redirects=True
        )
        return True
    return False

def test_1_global_admin_dashboard():
    """Test 1: Global admin dashboard accessible."""
    print("\n" + "="*70)
    print("TEST 1: Global Admin Dashboard Access")
    print("="*70)

    session = requests.Session()

    # Try without login
    response = session.get(f"{BASE_URL}/admin/global")
    if response.status_code != 401:
        print(f"❌ FAILED - Expected 401 for unauthorized access, got {response.status_code}")
        return False

    print(f"✅ Unauthorized access blocked (401)")

    # Login as admin
    if not login_as_admin(session):
        print(f"❌ FAILED - Could not login as admin")
        return False

    print(f"✅ Logged in as admin")

    # Try with login
    response = session.get(f"{BASE_URL}/admin/global")
    if response.status_code != 200:
        print(f"❌ FAILED - Expected 200 for authorized access, got {response.status_code}")
        return False

    if 'Global Admin' not in response.text:
        print(f"❌ FAILED - Global Admin page content not found")
        return False

    print(f"✅ Global admin dashboard accessible (200 OK)")

    print("\n✅ TEST 1 PASSED")
    return True

def test_2_create_event():
    """Test 2: Create a new event."""
    print("\n" + "="*70)
    print("TEST 2: Create New Event")
    print("="*70)

    session = requests.Session()
    login_as_admin(session)

    # Create event
    data = {
        'name': 'Paris 2024',
        'slug': 'paris-2024',
        'description': 'XXXIII Summer Olympic Games',
        'start_date': '2024-07-26',
        'end_date': '2024-08-11',
        'is_active': 'on'
    }

    print(f"\n📝 Creating event: {data['name']}")
    response = session.post(f"{BASE_URL}/admin/global/events/create", data=data, allow_redirects=False)

    if response.status_code != 302:
        print(f"❌ FAILED - Expected redirect (302), got {response.status_code}")
        return False

    print(f"✅ Event creation redirect successful")

    # Verify in database
    db = get_db()
    event = db.execute('SELECT * FROM events WHERE slug = ?', ['paris-2024']).fetchone()

    if not event:
        print(f"❌ FAILED - Event not found in database")
        db.close()
        return False

    print(f"✅ Event created in database:")
    print(f"   - ID: {event['id']}")
    print(f"   - Name: {event['name']}")
    print(f"   - Slug: {event['slug']}")
    print(f"   - Active: {event['is_active']}")

    db.close()

    print("\n✅ TEST 2 PASSED")
    return True

def test_3_create_contest():
    """Test 3: Create a new contest."""
    print("\n" + "="*70)
    print("TEST 3: Create New Contest")
    print("="*70)

    session = requests.Session()
    login_as_admin(session)

    # Get event ID for Milano 2026
    db = get_db()
    event = db.execute('SELECT id FROM events WHERE slug = ?', ['milano-2026']).fetchone()
    event_id = event['id']
    db.close()

    # Create contest
    data = {
        'event_id': str(event_id),
        'slug': 'family-pool',
        'name': 'Family Pool',
        'description': 'Family competition',
        'state': 'open',
        'budget': '250',
        'max_countries': '12',
        'deadline': '2026-02-04T23:59'
    }

    print(f"\n📝 Creating contest: {data['name']}")
    response = session.post(f"{BASE_URL}/admin/global/contests/create", data=data, allow_redirects=False)

    if response.status_code != 302:
        print(f"❌ FAILED - Expected redirect (302), got {response.status_code}")
        return False

    print(f"✅ Contest creation redirect successful")

    # Verify in database
    db = get_db()
    contest = db.execute('SELECT * FROM contest WHERE slug = ?', ['family-pool']).fetchone()

    if not contest:
        print(f"❌ FAILED - Contest not found in database")
        db.close()
        return False

    print(f"✅ Contest created in database:")
    print(f"   - ID: {contest['id']}")
    print(f"   - Name: {contest['name']}")
    print(f"   - Slug: {contest['slug']}")
    print(f"   - Budget: {contest['budget']}")
    print(f"   - Max Countries: {contest['max_countries']}")

    db.close()

    print("\n✅ TEST 3 PASSED")
    return True

def test_4_list_events_and_contests():
    """Test 4: List all events and contests."""
    print("\n" + "="*70)
    print("TEST 4: List Events and Contests")
    print("="*70)

    session = requests.Session()
    login_as_admin(session)

    # List events
    response = session.get(f"{BASE_URL}/admin/global/events")
    if response.status_code != 200:
        print(f"❌ FAILED - Events list returned {response.status_code}")
        return False

    if 'Milano Cortina 2026' not in response.text:
        print(f"❌ FAILED - Default event not in events list")
        return False

    print(f"✅ Events list accessible")

    # List contests
    response = session.get(f"{BASE_URL}/admin/global/contests")
    if response.status_code != 200:
        print(f"❌ FAILED - Contests list returned {response.status_code}")
        return False

    if 'XXV Winter Olympic Games' not in response.text:
        print(f"❌ FAILED - Default contest not in contests list")
        return False

    print(f"✅ Contests list accessible")

    print("\n✅ TEST 4 PASSED")
    return True

def test_5_navigation_link():
    """Test 5: Global Admin link in navigation."""
    print("\n" + "="*70)
    print("TEST 5: Global Admin Navigation Link")
    print("="*70)

    session = requests.Session()
    login_as_admin(session)

    # Visit contest page
    response = session.get(f"{BASE_URL}/milano-2026/default")

    if '🌐 Global Admin' not in response.text:
        print(f"❌ FAILED - Global Admin link not in navigation")
        return False

    print(f"✅ Global Admin link visible in navigation")

    print("\n✅ TEST 5 PASSED")
    return True

def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("GLOBAL ADMIN TEST SUITE")
    print("Multi-Contest Migration - OlympicPool2")
    print("="*70)

    # Note: Each test creates its own session and logs in independently
    # This mimics real-world usage where each page visit might be a separate session
    tests = [
        test_1_global_admin_dashboard,
        test_2_create_event,
        test_3_create_contest,
        test_4_list_events_and_contests,
        test_5_navigation_link,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            result = test()
            if result or result is None:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Total: {passed + failed}")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\nGlobal Admin Features:")
        print("  - Create/edit events")
        print("  - Create/edit contests")
        print("  - System-wide overview")
        print("  - Accessible at: /admin/global")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1

if __name__ == '__main__':
    exit(main())
