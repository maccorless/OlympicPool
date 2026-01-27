#!/usr/bin/env python3
"""
Test SMS/OTP authentication flow for multi-contest migration.
"""
import sqlite3
import requests
import re
from datetime import datetime

BASE_URL = "http://127.0.0.1:5002"
DB_PATH = "instance/medal_pool.db"

def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def test_1_registration_with_phone():
    """Test 1: Registration captures phone number and creates user + user_contest_info."""
    print("\n" + "="*70)
    print("TEST 1: Registration with Phone Number")
    print("="*70)

    # Register new user
    session = requests.Session()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    data = {
        'name': f'Test User {timestamp}',
        'email': f'test{timestamp}@example.com',
        'phone': '+12065551234',
        'team_name': f'Test Team {timestamp}'
    }

    print(f"\n📝 Registering user: {data['email']}")
    response = session.post(f"{BASE_URL}/milano-2026/default/register", data=data, allow_redirects=False)

    if response.status_code != 302:
        print(f"❌ FAILED - Expected redirect (302), got {response.status_code}")
        return False

    print(f"✅ Registration redirect successful")

    # Verify user in database
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', [data['email']]).fetchone()

    if not user:
        print(f"❌ FAILED - User not created in database")
        return False

    print(f"✅ User created in database (ID: {user['id']})")

    # Verify phone_number field exists and is correct
    if user['phone_number'] != '+12065551234':
        print(f"❌ FAILED - Phone number incorrect: {user['phone_number']}")
        return False

    print(f"✅ Phone number stored correctly: {user['phone_number']}")

    # Verify team_name is in users table (not user_contest_info)
    if user['team_name'] != data['team_name']:
        print(f"❌ FAILED - Team name not in users table")
        return False

    print(f"✅ Team name stored in users table: {user['team_name']}")

    # Verify user_contest_info created
    uci = db.execute(
        'SELECT * FROM user_contest_info WHERE user_id = ? AND contest_id = 1',
        [user['id']]
    ).fetchone()

    if not uci:
        print(f"❌ FAILED - user_contest_info not created")
        return False

    print(f"✅ User registered for contest (user_contest_info created)")

    # Verify user_contest_info does NOT have team_name column
    try:
        _ = uci['team_name']
        print(f"❌ FAILED - user_contest_info should NOT have team_name column")
        return False
    except (IndexError, KeyError):
        print(f"✅ user_contest_info correctly does NOT have team_name column")

    db.close()

    print("\n✅ TEST 1 PASSED")
    return True

def test_2_login_with_email_triggers_otp():
    """Test 2: Login with email triggers OTP generation."""
    print("\n" + "="*70)
    print("TEST 2: Login with Email Triggers OTP")
    print("="*70)

    # Create a test user first
    db = get_db()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    email = f'test_login_{timestamp}@example.com'

    db.execute('''
        INSERT INTO users (email, phone_number, name, team_name)
        VALUES (?, ?, ?, ?)
    ''', [email, '+12065559999', 'Login Test User', 'Login Test Team'])
    db.commit()

    user = db.execute('SELECT * FROM users WHERE email = ?', [email]).fetchone()
    user_id = user['id']

    # Join user to contest
    db.execute('INSERT INTO user_contest_info (user_id, contest_id) VALUES (?, 1)', [user_id])
    db.commit()
    db.close()

    print(f"\n📝 Test user created: {email}")

    # Try to login
    session = requests.Session()
    response = session.post(
        f"{BASE_URL}/milano-2026/default/login",
        data={'identifier': email},
        allow_redirects=True
    )

    # In NO_SMS_MODE, should render login_verify.html with OTP displayed
    if 'Verify Your Device' not in response.text:
        print(f"❌ FAILED - Did not reach verification page")
        return False

    print(f"✅ Redirected to verification page")

    # Extract OTP code from page (DEV MODE display)
    otp_match = re.search(r'<p class="text-4xl font-mono font-bold text-center text-yellow-900">(\d{4})</p>', response.text)

    if not otp_match:
        print(f"❌ FAILED - OTP code not displayed on page (NO_SMS_MODE may not be enabled)")
        return False

    otp_code = otp_match.group(1)
    print(f"✅ OTP code displayed in dev mode: {otp_code}")

    # Verify OTP in database
    db = get_db()
    otp_record = db.execute('''
        SELECT * FROM otp_codes
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    ''', [user_id]).fetchone()

    if not otp_record:
        print(f"❌ FAILED - OTP not created in database")
        db.close()
        return False

    print(f"✅ OTP record created in database (expires_at: {otp_record['expires_at']})")

    # Verify code_hash
    import hashlib
    expected_hash = hashlib.sha256(otp_code.encode()).hexdigest()
    if otp_record['code_hash'] != expected_hash:
        print(f"❌ FAILED - OTP hash mismatch")
        db.close()
        return False

    print(f"✅ OTP hash matches")

    db.close()

    print("\n✅ TEST 2 PASSED")
    return True, otp_code, email

def test_3_otp_verification_and_contest_redirect():
    """Test 3: OTP verification logs in user and redirects to contest."""
    print("\n" + "="*70)
    print("TEST 3: OTP Verification and Contest Redirect")
    print("="*70)

    # Create a test user
    db = get_db()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    email = f'test_verify_{timestamp}@example.com'

    db.execute('''
        INSERT INTO users (email, phone_number, name, team_name)
        VALUES (?, ?, ?, ?)
    ''', [email, '+12065558888', 'Verify Test User', 'Verify Test Team'])
    db.commit()

    user = db.execute('SELECT * FROM users WHERE email = ?', [email]).fetchone()
    user_id = user['id']

    # Join user to contest
    db.execute('INSERT INTO user_contest_info (user_id, contest_id) VALUES (?, 1)', [user_id])
    db.commit()
    db.close()

    print(f"\n📝 Test user created: {email}")

    # Use SAME session throughout (important for session cookie preservation)
    session = requests.Session()

    # Login to trigger OTP
    response = session.post(
        f"{BASE_URL}/milano-2026/default/login",
        data={'identifier': email},
        allow_redirects=True
    )

    # Extract OTP code from page
    otp_match = re.search(r'<p class="text-4xl font-mono font-bold text-center text-yellow-900">(\d{4})</p>', response.text)
    if not otp_match:
        print(f"❌ FAILED - Could not extract OTP code")
        return False

    otp_code = otp_match.group(1)
    print(f"✅ OTP code: {otp_code}")

    # Now submit OTP using SAME session
    print(f"📝 Submitting OTP: {otp_code}")
    response = session.post(
        f"{BASE_URL}/milano-2026/default/login/verify",
        data={'otp_code': otp_code},
        allow_redirects=False
    )

    if response.status_code != 302:
        print(f"❌ FAILED - Expected redirect after OTP verification, got {response.status_code}")
        return False

    # Check redirect location
    redirect_url = response.headers.get('Location', '')
    if '/milano-2026/default' not in redirect_url:
        print(f"❌ FAILED - Did not redirect to contest. Redirect: {redirect_url}")
        return False

    print(f"✅ Redirected to contest: {redirect_url}")

    # Verify OTP marked as used (add small delay to ensure DB write completes)
    import time
    time.sleep(0.1)

    db = get_db()
    otp_record = db.execute('''
        SELECT * FROM otp_codes
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    ''', [user_id]).fetchone()

    if not otp_record['used_at']:
        print(f"❌ FAILED - OTP not marked as used")
        print(f"   Debug: OTP record = {dict(otp_record)}")
        db.close()
        return False

    print(f"✅ OTP marked as used at: {otp_record['used_at']}")

    db.close()

    print("\n✅ TEST 3 PASSED")
    return True

def test_4_phone_not_unique():
    """Test 4: Same phone number can be used for multiple accounts."""
    print("\n" + "="*70)
    print("TEST 4: Phone Numbers NOT Unique (Multiple Accounts)")
    print("="*70)

    db = get_db()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    shared_phone = '+12065551111'

    # Create first user
    email1 = f'work_{timestamp}@example.com'
    db.execute('''
        INSERT INTO users (email, phone_number, name, team_name)
        VALUES (?, ?, ?, ?)
    ''', [email1, shared_phone, 'User 1', 'Team Work'])

    user1_id = db.execute('SELECT id FROM users WHERE email = ?', [email1]).fetchone()['id']
    print(f"✅ User 1 created: {email1} with phone {shared_phone}")

    # Create second user with SAME phone
    email2 = f'personal_{timestamp}@example.com'
    try:
        db.execute('''
            INSERT INTO users (email, phone_number, name, team_name)
            VALUES (?, ?, ?, ?)
        ''', [email2, shared_phone, 'User 2', 'Team Personal'])
        db.commit()

        user2_id = db.execute('SELECT id FROM users WHERE email = ?', [email2]).fetchone()['id']
        print(f"✅ User 2 created: {email2} with SAME phone {shared_phone}")

    except sqlite3.IntegrityError as e:
        print(f"❌ FAILED - Phone number constraint violated: {e}")
        db.close()
        return False

    # Verify both users exist with same phone
    users_with_phone = db.execute(
        'SELECT id, email FROM users WHERE phone_number = ?',
        [shared_phone]
    ).fetchall()

    if len(users_with_phone) < 2:
        print(f"❌ FAILED - Expected at least 2 users with phone {shared_phone}, found {len(users_with_phone)}")
        db.close()
        return False

    # Check that both our test users are in the list
    test_emails = {email1, email2}
    found_emails = {u['email'] for u in users_with_phone}

    if not test_emails.issubset(found_emails):
        print(f"❌ FAILED - Could not find both test users in results")
        db.close()
        return False

    print(f"✅ Both test users exist with same phone number:")
    for user in users_with_phone:
        if user['email'] in test_emails:
            print(f"   - ID {user['id']}: {user['email']}")

    db.close()

    print("\n✅ TEST 4 PASSED")
    return True

def test_5_existing_user_already_in_contest():
    """Test 5: Existing user trying to register for same contest shows error."""
    print("\n" + "="*70)
    print("TEST 5: Existing User Already in Contest")
    print("="*70)

    # Create test user
    db = get_db()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    email = f'existing_{timestamp}@example.com'

    db.execute('''
        INSERT INTO users (email, phone_number, name, team_name)
        VALUES (?, ?, ?, ?)
    ''', [email, '+12065552222', 'Existing User', 'Existing Team'])
    db.commit()

    user = db.execute('SELECT id FROM users WHERE email = ?', [email]).fetchone()
    user_id = user['id']

    # Join contest
    db.execute('INSERT INTO user_contest_info (user_id, contest_id) VALUES (?, 1)', [user_id])
    db.commit()
    db.close()

    print(f"✅ User already registered for contest: {email}")

    # Try to register again
    session = requests.Session()
    response = session.post(
        f"{BASE_URL}/milano-2026/default/register",
        data={
            'name': 'Existing User',
            'email': email,
            'phone': '+12065552222',
            'team_name': 'Duplicate Team'
        },
        allow_redirects=True
    )

    # Should show error message
    if 'already registered for this contest' not in response.text.lower():
        print(f"❌ FAILED - Did not show 'already registered' error")
        return False

    print(f"✅ Error message displayed for duplicate registration")

    print("\n✅ TEST 5 PASSED")
    return True

def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("SMS/OTP AUTHENTICATION TEST SUITE")
    print("Multi-Contest Migration - OlympicPool2")
    print("="*70)

    tests = [
        test_1_registration_with_phone,
        test_4_phone_not_unique,
        test_5_existing_user_already_in_contest,
        test_3_otp_verification_and_contest_redirect,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            result = test()
            if result or result is None:  # None means test passed without explicit return
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
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1

if __name__ == '__main__':
    exit(main())
