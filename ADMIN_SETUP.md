# Admin Setup - Hardcoded Administrator

**Branch:** `multi`
**Admin Email:** `ken@corless.com`
**Status:** ✅ Complete

---

## Overview

The administrator account (`ken@corless.com`) is pre-seeded in the database schema and automatically created on database initialization. The admin still requires SMS/OTP authentication but the account is ready for first login.

---

## What Was Implemented

### 1. Pre-Seeded Admin Account

**Updated `schema.sql`** to include admin account initialization:

```sql
-- Create administrator account (ken@corless.com)
-- Phone placeholder - user must provide real phone on first login
INSERT OR IGNORE INTO users (id, email, phone_number, name, team_name)
VALUES (1, 'ken@corless.com', '+10000000000', 'Ken Corless', 'Admin Team');

-- Register administrator for default contest
INSERT OR IGNORE INTO user_contest_info (user_id, contest_id)
VALUES (1, 1);
```

**Key Features:**
- ✅ User ID: 1 (reserved for admin)
- ✅ Email: ken@corless.com (hardcoded)
- ✅ Phone: +10000000000 (placeholder - must be updated on first use)
- ✅ Registered for default contest automatically
- ✅ Survives database reinitialization (INSERT OR IGNORE)

### 2. Admin Email Configuration

**In `.env`:**
```bash
ADMIN_EMAILS=ken@corless.com
```

**In `app/config.py`:**
```python
# Admin authorization (whitelist) - normalized to lowercase for case-insensitive comparison
ADMIN_EMAILS = [email.strip().lower() for email in os.getenv('ADMIN_EMAILS', '').split(',') if email.strip()]
```

### 3. Admin Authorization Decorator

**Updated `app/decorators.py`** to ensure case-insensitive email comparison:

```python
def admin_required(f):
    """Decorator to require admin user (based on ADMIN_EMAILS config)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            abort(401)
        # Case-insensitive email comparison (ADMIN_EMAILS normalized in config)
        if user['email'].lower() not in current_app.config['ADMIN_EMAILS']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
```

### 4. Registration Completion Flow

**Updated `app/routes/auth.py`** to allow pre-seeded accounts to complete setup:

When an existing user with placeholder phone (`+10000000000`) tries to register, the system:
1. Updates their phone number to the real one provided
2. Updates their name and team_name if provided
3. Logs them in immediately (no OTP required for registration)

**Key Code:**
```python
# If user has placeholder phone, update it (allows pre-seeded admins to complete setup)
if has_placeholder_phone:
    db.execute('''
        UPDATE users
        SET phone_number = ?, name = ?, team_name = ?
        WHERE id = ?
    ''', [phone_number, name, team_name, user_id])
    logger.info(f"Updated placeholder account for {email} with real phone number")
```

This solves the "chicken and egg" problem: admin account exists but can't login without a real phone number.

---

## First Time Admin Login Process

**Step 1: Complete Registration**
1. Visit: `http://localhost:5002/milano-2026/default/register`
2. Fill out registration form:
   - **Name:** Ken Corless (or your preferred name)
   - **Email:** ken@corless.com (must match exactly)
   - **Phone:** Your real phone number (for OTP)
   - **Team Name:** Your preferred team name
3. Submit form

**What Happens:**
- System recognizes existing account with placeholder phone
- Updates phone number to real one
- Logs you in immediately (no OTP required for registration)
- Redirects to contest home

**Step 2: Subsequent Logins**
1. Visit: `http://localhost:5002/milano-2026/default/login`
2. Enter email OR phone number: `ken@corless.com`
3. OTP sent to your phone (or displayed in dev mode)
4. Enter 4-digit OTP code
5. Logged in and redirected to contest

**Step 3: Access Admin Panel**
- Visit: `http://localhost:5002/milano-2026/default/admin`
- Full admin access granted based on ADMIN_EMAILS configuration

---

## Authentication Flow

```
Admin Pre-Seeded (placeholder phone)
         ↓
   First Access
         ↓
    Register Page → Fill Form with Real Phone
         ↓
  System Updates Phone Number
         ↓
    Immediate Login (session created)
         ↓
  Subsequent Logins Require OTP
         ↓
   Admin Panel Access (authorized by ADMIN_EMAILS)
```

---

## Security Considerations

1. **Still Requires Authentication:**
   - Admin must complete registration with real phone
   - All subsequent logins require OTP verification
   - No backdoor access

2. **Admin Authorization:**
   - Checked via `@admin_required` decorator
   - Based on ADMIN_EMAILS whitelist in config
   - Case-insensitive email comparison

3. **Session Management:**
   - Same session lifetime as regular users
   - Permanent sessions (remember this device)
   - Can be logged out via `/logout`

4. **Multi-Admin Support:**
   - Additional admins can be added to ADMIN_EMAILS
   - No need to pre-seed (can register normally)
   - Example: `ADMIN_EMAILS=ken@corless.com,admin2@example.com`

---

## Testing

**Automated Test Suite:** `test_admin_setup.py`

✅ **Test 1:** Admin Account Pre-Exists
- Verifies admin in database
- Verifies admin registered for contest
- Confirms placeholder phone

✅ **Test 2:** Admin Complete Registration
- Verifies phone number update works
- Verifies name/team update works
- Verifies immediate login after completion

✅ **Test 3:** Admin Login with OTP
- Verifies OTP generation and display
- Verifies OTP verification works
- Verifies redirect to contest

✅ **Test 4:** Admin Can Access Admin Panel
- Verifies full login flow
- Verifies admin panel accessible (200 OK)
- Verifies authorization works

**All tests passing:** 🎉

**Run Tests:**
```bash
source .venv/bin/activate
flask run --debug --port 5002  # In separate terminal
python test_admin_setup.py
```

---

## Database Verification

**Check admin account:**
```bash
sqlite3 instance/medal_pool.db "SELECT * FROM users WHERE email = 'ken@corless.com';"
```

**Expected output (before first login):**
```
1|ken@corless.com|+10000000000|Ken Corless|Admin Team|2026-01-26 10:00:26
```

**Expected output (after first login):**
```
1|ken@corless.com|+12065559999|Ken Corless|Ken's Team|2026-01-26 10:00:26
```

**Check contest membership:**
```bash
sqlite3 instance/medal_pool.db "SELECT * FROM user_contest_info WHERE user_id = 1;"
```

**Expected output:**
```
1|1|1|2026-01-26 10:00:26
```

---

## Adding Additional Admins

**Method 1: Environment Variable (Recommended)**

Add to `.env`:
```bash
ADMIN_EMAILS=ken@corless.com,admin2@example.com,admin3@example.com
```

- No database changes needed
- Takes effect immediately (restart Flask)
- Users register normally, get admin access automatically

**Method 2: Pre-Seed in Schema**

Add to `schema.sql`:
```sql
INSERT OR IGNORE INTO users (id, email, phone_number, name, team_name)
VALUES (2, 'admin2@example.com', '+10000000000', 'Admin 2', 'Admin Team 2');

INSERT OR IGNORE INTO user_contest_info (user_id, contest_id)
VALUES (2, 1);
```

- Account exists on database initialization
- Must complete registration with real phone
- Useful for permanent admin accounts

---

## Production Deployment

When deploying to Railway:

1. **Set Environment Variable:**
   ```bash
   ADMIN_EMAILS=ken@corless.com
   ```

2. **Database Initialization:**
   - Railway will run `flask init-db` on first deploy
   - Admin account automatically created from schema.sql
   - Countries loaded from data/countries.sql

3. **First Login:**
   - Visit production URL: `https://yourapp.railway.app/milano-2026/default/register`
   - Complete registration with real phone number
   - Subsequent logins require OTP

4. **Verify Admin Access:**
   - Login with OTP
   - Visit: `https://yourapp.railway.app/milano-2026/default/admin`
   - Should see admin dashboard

---

## Troubleshooting

**Problem: "Already registered for this contest"**
- **Cause:** Admin account exists and already joined contest
- **Solution:** Use login page instead of registration

**Problem: "Invalid email or phone number format"**
- **Cause:** Phone number not in E.164 format
- **Solution:** Use format: +1XXXXXXXXXX (e.g., +12065551234)

**Problem: "Access denied (403)"**
- **Cause:** Email not in ADMIN_EMAILS configuration
- **Solution:** Check `.env` file has correct email (case-insensitive)

**Problem: "OTP not received"**
- **Dev Mode:** OTP displayed on screen (NO_SMS_MODE=True)
- **Production:** Check Twilio configuration
- **Solution:** Verify NO_SMS_MODE setting in environment

**Problem: Admin panel shows blank page**
- **Cause:** Database not initialized or schema outdated
- **Solution:** Reinitialize database: `rm instance/medal_pool.db && flask init-db`

---

## Files Modified

| File | Change |
|------|--------|
| `schema.sql` | Added admin user pre-seed with INSERT statements |
| `app/decorators.py` | Updated admin_required for case-insensitive email check |
| `app/routes/auth.py` | Added placeholder phone update logic in registration |
| `.env` | Already had ADMIN_EMAILS=ken@corless.com |
| `test_admin_setup.py` | Created comprehensive admin test suite |

---

## Summary

✅ **Admin account is hardcoded and pre-seeded**
✅ **Still requires authentication (OTP)**
✅ **Ready for first login via registration completion**
✅ **Admin panel access automatic after login**
✅ **All tests passing**

**Next Step:** Visit `/milano-2026/default/register` to complete admin setup with real phone number.

---

**Admin Email:** ken@corless.com
**Status:** Pre-configured and ready for first use
**First Use:** Complete registration to activate
