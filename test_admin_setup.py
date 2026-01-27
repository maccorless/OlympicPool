#!/usr/bin/env python3
"""
Test admin account setup and authentication.
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

def test_1_admin_account_exists():
    """Test 1: Verify admin account pre-exists in database."""
    print("\n" + "="*70)
    print("TEST 1: Admin Account Pre-Exists")
    print("="*70)

    db = get_db()
    admin = db.execute('SELECT * FROM users WHERE email = ?', ['ken@corless.com']).fetchone()

    if not admin:
        print("❌ FAILED - Admin account not found")
        db.close()
        return False

    print(f"✅ Admin account exists:")
    print(f"   - ID: {admin['id']}")
    print(f"   - Email: {admin['email']}")
    print(f"   - Name: {admin['name']}")
    print(f"   - Team: {admin['team_name']}")
    print(f"   - Phone: {admin['phone_number']}")

    # Check if admin is in contest
    contest_membership = db.execute('''
        SELECT * FROM user_contest_info WHERE user_id = ? AND contest_id = 1
    ''', [admin['id']]).fetchone()

    if not contest_membership:
        print("❌ FAILED - Admin not registered for default contest")
        db.close()
        return False

    print(f"✅ Admin registered for default contest")

    # Check if phone is placeholder
    if admin['phone_number'] == '+10000000000':
        print(f"⚠️  Phone number is placeholder - admin needs to complete registration")
    else:
        print(f"✅ Real phone number provided")

    db.close()

    print("\n✅ TEST 1 PASSED")
    return True

def test_2_admin_complete_registration():
    """Test 2: Admin can complete registration with real phone number."""
    print("\n" + "="*70)
    print("TEST 2: Admin Complete Registration")
    print("="*70)

    session = requests.Session()

    # Admin "registers" to complete setup
    data = {
        'name': 'Ken Corless',
        'email': 'ken@corless.com',
        'phone': '+12065559999',
        'team_name': 'Ken\'s Team'
    }

    print(f"\n📝 Completing registration for admin: {data['email']}")
    response = session.post(f"{BASE_URL}/milano-2026/default/register", data=data, allow_redirects=False)

    if response.status_code != 302:
        print(f"❌ FAILED - Expected redirect (302), got {response.status_code}")
        return False

    print(f"✅ Registration completed successfully")

    # Verify phone number updated
    db = get_db()
    admin = db.execute('SELECT * FROM users WHERE email = ?', ['ken@corless.com']).fetchone()

    if admin['phone_number'] != '+12065559999':
        print(f"❌ FAILED - Phone number not updated: {admin['phone_number']}")
        db.close()
        return False

    print(f"✅ Phone number updated: {admin['phone_number']}")

    # Verify name/team updated
    if admin['name'] != data['name'] or admin['team_name'] != data['team_name']:
        print(f"❌ FAILED - Name or team not updated")
        db.close()
        return False

    print(f"✅ Name and team updated")
    print(f"   - Name: {admin['name']}")
    print(f"   - Team: {admin['team_name']}")

    db.close()

    print("\n✅ TEST 2 PASSED")
    return True

def test_3_admin_login_with_otp():
    """Test 3: Admin can login with OTP."""
    print("\n" + "="*70)
    print("TEST 3: Admin Login with OTP")
    print("="*70)

    # Make sure admin has real phone (from test 2)
    db = get_db()
    admin = db.execute('SELECT * FROM users WHERE email = ?', ['ken@corless.com']).fetchone()

    if admin['phone_number'] == '+10000000000':
        print("⚠️  Skipping - admin needs real phone number (run test 2 first)")
        db.close()
        return True

    print(f"📝 Admin phone: {admin['phone_number']}")

    # Login with email
    session = requests.Session()
    response = session.post(
        f"{BASE_URL}/milano-2026/default/login",
        data={'identifier': 'ken@corless.com'},
        allow_redirects=True
    )

    if 'Verify Your Device' not in response.text:
        print(f"❌ FAILED - Did not reach OTP verification page")
        db.close()
        return False

    print(f"✅ OTP verification page loaded")

    # Extract OTP code
    otp_match = re.search(r'<p class="text-4xl font-mono font-bold text-center text-yellow-900">(\d{4})</p>', response.text)

    if not otp_match:
        print(f"❌ FAILED - OTP code not displayed (NO_SMS_MODE may not be enabled)")
        db.close()
        return False

    otp_code = otp_match.group(1)
    print(f"✅ OTP code: {otp_code}")

    # Submit OTP
    response = session.post(
        f"{BASE_URL}/milano-2026/default/login/verify",
        data={'otp_code': otp_code},
        allow_redirects=False
    )

    if response.status_code != 302:
        print(f"❌ FAILED - OTP verification failed, got {response.status_code}")
        db.close()
        return False

    redirect_url = response.headers.get('Location', '')
    if '/milano-2026/default' not in redirect_url:
        print(f"❌ FAILED - Did not redirect to contest: {redirect_url}")
        db.close()
        return False

    print(f"✅ OTP verified, redirected to contest")

    db.close()

    print("\n✅ TEST 3 PASSED")
    return True

def test_4_admin_can_access_admin_panel():
    """Test 4: Admin can access admin panel."""
    print("\n" + "="*70)
    print("TEST 4: Admin Can Access Admin Panel")
    print("="*70)

    # Login first
    session = requests.Session()

    # Complete registration if needed
    db = get_db()
    admin = db.execute('SELECT * FROM users WHERE email = ?', ['ken@corless.com']).fetchone()
    if admin['phone_number'] == '+10000000000':
        # Complete registration
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

    otp_match = re.search(r'<p class="text-4xl font-mono font-bold text-center text-yellow-900">(\d{4})</p>', response.text)
    if otp_match:
        otp_code = otp_match.group(1)
        session.post(
            f"{BASE_URL}/milano-2026/default/login/verify",
            data={'otp_code': otp_code},
            allow_redirects=True
        )

    # Try to access admin panel
    response = session.get(f"{BASE_URL}/milano-2026/default/admin", allow_redirects=False)

    if response.status_code == 403:
        print(f"❌ FAILED - Access denied (403) - admin authorization not working")
        return False

    if response.status_code == 401:
        print(f"❌ FAILED - Unauthorized (401) - session not established")
        return False

    if response.status_code != 200:
        print(f"❌ FAILED - Unexpected status code: {response.status_code}")
        return False

    if 'Admin Dashboard' not in response.text and 'admin' not in response.text.lower():
        print(f"❌ FAILED - Admin panel content not found")
        return False

    print(f"✅ Admin panel accessible (200 OK)")

    print("\n✅ TEST 4 PASSED")
    return True

def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("ADMIN SETUP TEST SUITE")
    print("Multi-Contest Migration - OlympicPool2")
    print("="*70)

    tests = [
        test_1_admin_account_exists,
        test_2_admin_complete_registration,
        test_3_admin_login_with_otp,
        test_4_admin_can_access_admin_panel,
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
        print("\nAdmin account ready:")
        print("  Email: ken@corless.com")
        print("  Status: Complete registration at /milano-2026/default/register")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1

if __name__ == '__main__':
    exit(main())
