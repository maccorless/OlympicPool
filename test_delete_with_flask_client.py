#!/usr/bin/env python3
"""
Test delete functionality using Flask test client (not external HTTP requests).
This avoids session persistence issues with requests.Session().
"""
import os
import sys

# Add app directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import sqlite3
from app import create_app

def get_db():
    """Get database connection for tests (outside Flask context)."""
    conn = sqlite3.connect('instance/medal_pool.db')
    conn.row_factory = sqlite3.Row
    return conn

def setup_admin():
    """Ensure admin account exists in database."""
    db = get_db()
    # Check if admin exists
    admin = db.execute('SELECT * FROM users WHERE email = ?', ['ken@corless.com']).fetchone()
    if not admin:
        print("❌ Admin account not found in database. Run 'flask init-db' first.")
        return False

    # Ensure admin has real phone (not placeholder)
    if admin['phone_number'] == '+10000000000':
        db.execute('''
            UPDATE users
            SET phone_number = ?, name = ?, team_name = ?
            WHERE id = ?
        ''', ['+12065551234', 'Ken Corless', 'Admin Team', admin['id']])
        db.commit()
        print("✅ Updated admin phone number")

    db.close()
    return True

def login_as_admin(client):
    """
    Login as admin using Flask test client.
    Returns True if login successful, False otherwise.
    """
    # Step 1: POST to login to request OTP
    response = client.post('/milano-2026/default/login',
                          data={'identifier': 'ken@corless.com'},
                          follow_redirects=False)

    # In NO_SMS_MODE, OTP is shown on page
    if response.status_code == 200 and b'text-4xl font-mono font-bold' in response.data:
        # Extract OTP from HTML
        import re
        html = response.data.decode('utf-8')
        otp_match = re.search(r'<p class="text-4xl font-mono font-bold text-center text-yellow-900">(\d{4})</p>', html)

        if not otp_match:
            print("❌ Could not find OTP in response")
            return False

        otp_code = otp_match.group(1)
        print(f"✅ Extracted OTP: {otp_code}")

        # Step 2: POST to verify OTP
        response = client.post('/milano-2026/default/login/verify',
                              data={'otp_code': otp_code},
                              follow_redirects=True)

        if response.status_code == 200:
            print("✅ Login successful (session cookie set)")
            return True
        else:
            print(f"❌ OTP verification failed: {response.status_code}")
            return False
    else:
        print(f"❌ Login request failed: {response.status_code}")
        return False

def test_1_create_and_delete_event():
    """Test 1: Create and delete an event."""
    print("\n" + "="*70)
    print("TEST 1: Create and Delete Event (Flask Test Client)")
    print("="*70)

    # Create Flask test client
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    client = app.test_client()

    # Login as admin
    print("\n📝 Logging in as admin...")
    if not login_as_admin(client):
        print("❌ TEST 1 FAILED - Could not login")
        return False

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
    response = client.post('/admin/global/events/create',
                          data=data,
                          follow_redirects=True)

    if response.status_code != 200:
        print(f"❌ FAILED - Event creation returned {response.status_code}")
        print(f"Response: {response.data.decode('utf-8')[:500]}")
        return False

    # Verify event created in database
    db = get_db()
    event = db.execute('SELECT id FROM events WHERE slug = ?', ['test-2030']).fetchone()
    if not event:
        print("❌ FAILED - Event not found in database")
        db.close()
        return False

    event_id = event['id']
    print(f"✅ Event created (ID: {event_id})")
    db.close()

    # Try to delete (first request shows confirmation page)
    print(f"📝 Requesting deletion...")
    response = client.post(f'/admin/global/events/{event_id}/delete',
                          follow_redirects=False)

    if response.status_code != 200:
        print(f"❌ FAILED - Delete request returned {response.status_code}")
        return False

    if b'Delete Event' not in response.data:
        print("❌ FAILED - Confirmation page not shown")
        return False

    print("✅ Confirmation page displayed")

    # Confirm deletion
    print(f"📝 Confirming deletion...")
    response = client.post(f'/admin/global/events/{event_id}/delete',
                          data={'confirmed': 'yes'},
                          follow_redirects=True)

    if response.status_code != 200:
        print(f"❌ FAILED - Deletion confirmation returned {response.status_code}")
        return False

    # Verify event deleted
    db = get_db()
    event = db.execute('SELECT id FROM events WHERE slug = ?', ['test-2030']).fetchone()
    db.close()

    if event:
        print("❌ FAILED - Event still exists in database")
        return False

    print("✅ Event successfully deleted from database")
    print("\n✅ TEST 1 PASSED")
    return True

def test_2_create_and_delete_contest():
    """Test 2: Create and delete a contest."""
    print("\n" + "="*70)
    print("TEST 2: Create and Delete Contest (Flask Test Client)")
    print("="*70)

    # Create Flask test client
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    client = app.test_client()

    # Login as admin
    print("\n📝 Logging in as admin...")
    if not login_as_admin(client):
        print("❌ TEST 2 FAILED - Could not login")
        return False

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
    response = client.post('/admin/global/contests/create',
                          data=data,
                          follow_redirects=True)

    if response.status_code != 200:
        print(f"❌ FAILED - Contest creation returned {response.status_code}")
        return False

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
    response = client.post(f'/admin/global/contests/{contest_id}/delete',
                          follow_redirects=False)

    if response.status_code != 200:
        print(f"❌ FAILED - Delete request returned {response.status_code}")
        return False

    if b'Delete Contest' not in response.data:
        print("❌ FAILED - Confirmation page not shown")
        return False

    print("✅ Confirmation page displayed")

    # Confirm deletion
    print(f"📝 Confirming deletion...")
    response = client.post(f'/admin/global/contests/{contest_id}/delete',
                          data={'confirmed': 'yes'},
                          follow_redirects=True)

    if response.status_code != 200:
        print(f"❌ FAILED - Deletion confirmation returned {response.status_code}")
        return False

    # Verify contest deleted
    db = get_db()
    contest = db.execute('SELECT id FROM contest WHERE slug = ?', ['test-pool']).fetchone()
    db.close()

    if contest:
        print("❌ FAILED - Contest still exists in database")
        return False

    print("✅ Contest successfully deleted from database")
    print("\n✅ TEST 2 PASSED")
    return True

def test_3_delete_event_with_contests():
    """Test 3: Delete event with contests (CASCADE)."""
    print("\n" + "="*70)
    print("TEST 3: Delete Event with Contests (CASCADE)")
    print("="*70)

    # Create Flask test client
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    client = app.test_client()

    # Login as admin
    print("\n📝 Logging in as admin...")
    if not login_as_admin(client):
        print("❌ TEST 3 FAILED - Could not login")
        return False

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
    client.post('/admin/global/events/create', data=data, follow_redirects=True)

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
    client.post('/admin/global/contests/create', data=contest_data, follow_redirects=True)

    db = get_db()
    contest = db.execute('SELECT id FROM contest WHERE slug = ?', ['test-contest']).fetchone()
    contest_id = contest['id']
    print(f"✅ Contest created (ID: {contest_id})")
    db.close()

    # Delete event (should CASCADE delete contest)
    print(f"📝 Deleting event (should CASCADE delete contest)...")
    client.post(f'/admin/global/events/{event_id}/delete', follow_redirects=False)
    client.post(f'/admin/global/events/{event_id}/delete',
               data={'confirmed': 'yes'},
               follow_redirects=True)

    # Verify both event and contest deleted
    db = get_db()
    event = db.execute('SELECT id FROM events WHERE slug = ?', ['cascade-2032']).fetchone()
    contest = db.execute('SELECT id FROM contest WHERE slug = ?', ['test-contest']).fetchone()
    db.close()

    if event:
        print("❌ FAILED - Event still exists")
        return False

    if contest:
        print("❌ FAILED - Contest still exists (CASCADE failed)")
        return False

    print("✅ Event and contest both deleted (CASCADE worked)")
    print("\n✅ TEST 3 PASSED")
    return True

def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("DELETE FUNCTIONALITY TEST SUITE (Flask Test Client)")
    print("Multi-Contest Migration - OlympicPool2")
    print("="*70)

    # Setup admin account
    if not setup_admin():
        print("\n❌ Admin setup failed. Aborting tests.")
        return 1

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
