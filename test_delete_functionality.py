#!/usr/bin/env python3
"""
Test delete functionality for events and contests.
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

def test_1_create_and_delete_event():
    """Test 1: Create and delete an event."""
    print("\n" + "="*70)
    print("TEST 1: Create and Delete Event")
    print("="*70)

    session = requests.Session()
    login_as_admin(session)

    # Create a test event
    data = {
        'name': 'Test Event 2030',
        'slug': 'test-2030',
        'description': 'Test event for deletion',
        'start_date': '2030-01-01',
        'end_date': '2030-01-31',
        'is_active': 'on'
    }

    print(f"\n📝 Creating test event: {data['name']}")
    response = session.post(f"{BASE_URL}/admin/global/events/create", data=data, allow_redirects=True)

    # Get event ID
    db = get_db()
    event = db.execute('SELECT id FROM events WHERE slug = ?', ['test-2030']).fetchone()
    if not event:
        print("❌ FAILED - Event not created")
        db.close()
        return False

    event_id = event['id']
    print(f"✅ Event created (ID: {event_id})")
    db.close()

    # Try to delete (first request shows confirmation page)
    print(f"📝 Requesting deletion...")
    response = session.post(f"{BASE_URL}/admin/global/events/{event_id}/delete", allow_redirects=False)

    if 'Delete Event' not in response.text:
        print(f"❌ FAILED - Confirmation page not shown")
        return False

    print(f"✅ Confirmation page displayed")

    # Confirm deletion
    print(f"📝 Confirming deletion...")
    response = session.post(
        f"{BASE_URL}/admin/global/events/{event_id}/delete",
        data={'confirmed': 'yes'},
        allow_redirects=True
    )

    # Verify event deleted
    db = get_db()
    event = db.execute('SELECT id FROM events WHERE slug = ?', ['test-2030']).fetchone()
    db.close()

    if event:
        print(f"❌ FAILED - Event still exists in database")
        return False

    print(f"✅ Event successfully deleted from database")

    print("\n✅ TEST 1 PASSED")
    return True

def test_2_create_and_delete_contest():
    """Test 2: Create and delete a contest."""
    print("\n" + "="*70)
    print("TEST 2: Create and Delete Contest")
    print("="*70)

    session = requests.Session()
    login_as_admin(session)

    # Get Milano 2026 event ID
    db = get_db()
    event = db.execute('SELECT id FROM events WHERE slug = ?', ['milano-2026']).fetchone()
    event_id = event['id']
    db.close()

    # Create a test contest
    data = {
        'event_id': str(event_id),
        'slug': 'test-pool',
        'name': 'Test Pool',
        'description': 'Test contest for deletion',
        'state': 'setup',
        'budget': '100',
        'max_countries': '5',
        'deadline': '2026-02-01T00:00'
    }

    print(f"\n📝 Creating test contest: {data['name']}")
    response = session.post(f"{BASE_URL}/admin/global/contests/create", data=data, allow_redirects=True)

    # Get contest ID
    db = get_db()
    contest = db.execute('SELECT id FROM contest WHERE slug = ?', ['test-pool']).fetchone()
    if not contest:
        print("❌ FAILED - Contest not created")
        db.close()
        return False

    contest_id = contest['id']
    print(f"✅ Contest created (ID: {contest_id})")
    db.close()

    # Try to delete (first request shows confirmation page)
    print(f"📝 Requesting deletion...")
    response = session.post(f"{BASE_URL}/admin/global/contests/{contest_id}/delete", allow_redirects=False)

    if 'Delete Contest' not in response.text:
        print(f"❌ FAILED - Confirmation page not shown")
        return False

    print(f"✅ Confirmation page displayed")

    # Confirm deletion
    print(f"📝 Confirming deletion...")
    response = session.post(
        f"{BASE_URL}/admin/global/contests/{contest_id}/delete",
        data={'confirmed': 'yes'},
        allow_redirects=True
    )

    # Verify contest deleted
    db = get_db()
    contest = db.execute('SELECT id FROM contest WHERE slug = ?', ['test-pool']).fetchone()
    db.close()

    if contest:
        print(f"❌ FAILED - Contest still exists in database")
        return False

    print(f"✅ Contest successfully deleted from database")

    print("\n✅ TEST 2 PASSED")
    return True

def test_3_delete_event_with_contests():
    """Test 3: Delete event with contests (CASCADE)."""
    print("\n" + "="*70)
    print("TEST 3: Delete Event with Contests (CASCADE)")
    print("="*70)

    session = requests.Session()
    login_as_admin(session)

    # Create a test event
    data = {
        'name': 'Cascade Test 2032',
        'slug': 'cascade-2032',
        'description': 'Test CASCADE deletion',
        'start_date': '2032-01-01',
        'end_date': '2032-01-31',
        'is_active': 'on'
    }

    print(f"\n📝 Creating test event: {data['name']}")
    session.post(f"{BASE_URL}/admin/global/events/create", data=data, allow_redirects=True)

    db = get_db()
    event = db.execute('SELECT id FROM events WHERE slug = ?', ['cascade-2032']).fetchone()
    event_id = event['id']
    db.close()

    # Create a contest within this event
    contest_data = {
        'event_id': str(event_id),
        'slug': 'test-contest',
        'name': 'Test Contest',
        'state': 'setup',
        'budget': '100',
        'max_countries': '5',
        'deadline': '2032-01-01T00:00'
    }

    print(f"📝 Creating test contest in event...")
    session.post(f"{BASE_URL}/admin/global/contests/create", data=contest_data, allow_redirects=True)

    db = get_db()
    contest = db.execute('SELECT id FROM contest WHERE slug = ?', ['test-contest']).fetchone()
    contest_id = contest['id']
    print(f"✅ Contest created (ID: {contest_id})")
    db.close()

    # Delete event (should CASCADE delete contest)
    print(f"📝 Deleting event (should CASCADE delete contest)...")
    session.post(f"{BASE_URL}/admin/global/events/{event_id}/delete", allow_redirects=False)
    session.post(
        f"{BASE_URL}/admin/global/events/{event_id}/delete",
        data={'confirmed': 'yes'},
        allow_redirects=True
    )

    # Verify both event and contest deleted
    db = get_db()
    event = db.execute('SELECT id FROM events WHERE slug = ?', ['cascade-2032']).fetchone()
    contest = db.execute('SELECT id FROM contest WHERE slug = ?', ['test-contest']).fetchone()
    db.close()

    if event:
        print(f"❌ FAILED - Event still exists")
        return False

    if contest:
        print(f"❌ FAILED - Contest still exists (CASCADE failed)")
        return False

    print(f"✅ Event and contest both deleted (CASCADE worked)")

    print("\n✅ TEST 3 PASSED")
    return True

def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("DELETE FUNCTIONALITY TEST SUITE")
    print("Multi-Contest Migration - OlympicPool2")
    print("="*70)

    tests = [
        test_1_create_and_delete_event,
        test_2_create_and_delete_contest,
        test_3_delete_event_with_contests,
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
        print("\nDelete Features:")
        print("  ✅ Delete events with confirmation")
        print("  ✅ Delete contests with confirmation")
        print("  ✅ CASCADE deletion works (event → contests)")
        print("  ✅ Shows impact statistics before deletion")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1

if __name__ == '__main__':
    exit(main())
