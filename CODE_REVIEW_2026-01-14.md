# Code Review - January 14, 2026

## Executive Summary

Reviewed 1,354 lines of Python code across routes, configuration, and database modules, plus templates. The codebase is well-structured with good separation of concerns, but has **one critical security vulnerability** and several moderate issues that should be addressed.

**Critical Priority:**
- ❌ **P0: No CSRF protection** on any POST endpoints

**High Priority:**
- ⚠️ **P1: Performance issue** - database query on every template render
- ⚠️ **P1: Production security** - session cookies not secure by default

**Moderate Priority:**
- 📋 **P2: Multiple code quality and UX improvements**

---

## Security Issues

### 🔴 P0: No CSRF Protection (CRITICAL)

**Issue:** All POST endpoints lack CSRF token validation.

**Affected Routes:**
- `/register` - User registration
- `/login` - Magic link requests
- `/draft/submit` - Draft submission
- `/admin/contest` - Contest configuration
- `/admin/countries/import` - Country data import
- `/admin/medals` - Medal entry
- `/admin/medals/bulk` - Bulk medal import

**Risk:** Attackers can perform state-changing actions on behalf of authenticated users via:
- Malicious links that auto-submit forms
- XSS attacks (if any are found)
- Social engineering

**Example Attack:**
```html
<!-- Attacker's website -->
<form action="https://yoursite.com/admin/medals" method="POST">
  <input type="hidden" name="gold_NOR" value="999">
  <!-- ... more fields ... -->
</form>
<script>document.forms[0].submit();</script>
```

If an admin visits this page while logged in, medals get updated without their knowledge.

**Recommendation:**
Install Flask-WTF and add CSRF protection:

```python
# app/__init__.py
from flask_wtf.csrf import CSRFProtect

def create_app():
    app = Flask(__name__)
    # ... existing config ...

    # Enable CSRF protection
    csrf = CSRFProtect(app)

    # ... rest of setup ...
```

Then add to all templates with POST forms:
```html
<form method="POST">
    {{ csrf_token() }}
    <!-- form fields -->
</form>
```

**Effort:** 2-3 hours (install package, add tokens to 7 forms, test)

---

### 🟡 P1: Session Cookies Not Secure in Production

**Issue:** `SESSION_COOKIE_SECURE` defaults to `False`

**Location:** `app/config.py:27`

```python
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
```

**Risk:** Session cookies can be intercepted over HTTP in production if HTTPS isn't enforced at reverse proxy level.

**Recommendation:**
Default to True for production safety:

```python
# Detect production environment
IS_PRODUCTION = os.getenv('FLASK_ENV') == 'production' or os.getenv('RAILWAY_ENVIRONMENT') is not None

SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', str(IS_PRODUCTION)).lower() == 'true'
```

Or set environment variable in Railway:
```
SESSION_COOKIE_SECURE=true
```

**Effort:** 15 minutes

---

### 🟡 P1: Weak Default SECRET_KEY

**Issue:** Default secret key is predictable

**Location:** `app/config.py:8`

```python
SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-for-local-testing-only')
```

**Risk:** If deployed without setting `FLASK_SECRET_KEY`, sessions can be forged.

**Recommendation:**
Fail loudly in production if secret key is not set:

```python
SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
if not SECRET_KEY:
    if IS_PRODUCTION:
        raise RuntimeError("FLASK_SECRET_KEY must be set in production")
    SECRET_KEY = 'dev-secret-key-for-local-testing-only'
```

**Effort:** 15 minutes

---

### ✅ SQL Injection - All Clear

**Review:** All dynamic SQL uses proper techniques:
- ✅ Parameterized queries for user data (`?` placeholders)
- ✅ F-strings only for structural elements (ORDER BY, IN clause placeholders)
- ✅ Whitelist validation before f-string usage (`valid_sorts`, `valid_states`)

**Examples of correct patterns:**
```python
# admin.py:290-294 - Whitelist validation
if sort_by not in valid_sorts:
    sort_by = 'name'

# admin.py:304-313 - Safe f-string usage after validation
order_clause = f'{sort_column} {sort_order.upper()}'
db.execute(f'... ORDER BY {order_clause}')

# draft.py:154 - Safe placeholder generation
placeholders = ','.join('?' * len(country_codes))  # Just '?', '?', '?'
db.execute(f'... WHERE code IN ({placeholders})', country_codes)
```

**No changes needed.**

---

## Performance Issues

### 🟡 P1: Database Query on Every Request

**Issue:** Context processor calls `get_current_user()` on every template render, executing a DB query even for unauthenticated users.

**Location:** `app/__init__.py:36-40`

```python
@app.context_processor
def inject_user():
    from app.decorators import get_current_user
    return {'user': get_current_user()}  # DB query on EVERY request
```

**Impact:**
- Extra DB query on every page load (even for logged-out users)
- Increases latency by ~5-15ms per request
- Unnecessary load on database

**Recommendation:**
Only query if session exists:

```python
@app.context_processor
def inject_user():
    from flask import session
    from app.decorators import get_current_user

    # Only query DB if user_id is in session
    if 'user_id' in session:
        return {'user': get_current_user()}
    return {'user': None}
```

Or better yet, cache in g:

```python
@app.context_processor
def inject_user():
    from flask import g
    from app.decorators import get_current_user

    # get_current_user already uses g, but we should cache the result
    if not hasattr(g, 'cached_user'):
        g.cached_user = get_current_user()
    return {'user': g.cached_user}
```

**Effort:** 30 minutes

---

### ✅ N+1 Queries - Fixed

**Review:** Leaderboard previously had N+1 issue fetching countries per team. **Already fixed** in `leaderboard.py:110-134`:

```python
# Single query for all teams' countries
user_ids = [team['id'] for team in teams]
placeholders = ','.join('?' * len(user_ids))
all_countries = db.execute(f'''
    SELECT p.user_id, c.code, c.iso_code, c.name
    FROM picks p
    JOIN countries c ON p.country_code = c.code
    WHERE p.user_id IN ({placeholders})
    ORDER BY p.user_id, c.name
''', user_ids).fetchall()

# Group in Python
countries_by_user = {}
for row in all_countries:
    user_id = row['user_id']
    if user_id not in countries_by_user:
        countries_by_user[user_id] = []
    countries_by_user[user_id].append({...})
```

**No changes needed.**

---

## Code Quality Issues

### 🟢 P2: Inconsistent Error Handling in Bulk Import

**Issue:** Overly broad exception catch in `admin_medals_bulk()`

**Location:** `app/routes/admin.py:453-456`

```python
except Exception as e:
    logger.error(f"Error parsing bulk medal data: {e}")
    flash(f'Error parsing data: {str(e)}', 'error')
    return redirect(url_for('admin_medals_bulk'))
```

**Risk:**
- Catches unexpected errors (e.g., programming bugs)
- Exposes internal error messages to users
- Makes debugging harder

**Recommendation:**
Catch specific exceptions:

```python
except (ValueError, IndexError, KeyError) as e:
    logger.error(f"Error parsing bulk medal data: {e}")
    flash('Error parsing data. Please check the format and try again.', 'error')
    return redirect(url_for('admin_medals_bulk'))
except Exception as e:
    logger.exception(f"Unexpected error in bulk medal import: {e}")
    flash('An unexpected error occurred. Please try again.', 'error')
    return redirect(url_for('admin_medals_bulk'))
```

**Effort:** 15 minutes

---

### 🟢 P2: Missing Input Validation - Negative Medal Counts

**Issue:** No validation preventing negative medal counts

**Location:** `app/routes/admin.py:232-242` and `admin.py:381-387`

**Current code:**
```python
try:
    count = int(value) if value else 0
    updates.append((medal_type, country_code, count))
except ValueError:
    flash(f'Invalid value for {country_code} {medal_type}.', 'error')
```

**Risk:** Admin could enter `-5` medals, creating invalid data.

**Recommendation:**
Add range validation:

```python
try:
    count = int(value) if value else 0
    if count < 0:
        flash(f'Medal counts cannot be negative ({country_code} {medal_type}).', 'error')
        return redirect(url_for('admin_medals'))
    updates.append((medal_type, country_code, count))
except ValueError:
    flash(f'Invalid value for {country_code} {medal_type}.', 'error')
    return redirect(url_for('admin_medals'))
```

Also add HTML validation:
```html
<input type="number" name="gold_{{ country.code }}" value="{{ country.gold }}" min="0" max="999">
```

**Effort:** 20 minutes

---

### 🟢 P2: Email Validation is Basic

**Issue:** Regex-less email validation in `is_valid_email()`

**Location:** `app/routes/auth.py:16-25`

```python
def is_valid_email(email):
    """Basic email validation: must have @, at least one . after @, no spaces."""
    if not email or ' ' in email:
        return False
    if '@' not in email:
        return False
    local, _, domain = email.partition('@')
    if not local or not domain or '.' not in domain:
        return False
    return True
```

**Edge Cases:**
- Accepts: `user@domain` (no TLD)
- Accepts: `user..name@domain.com` (consecutive dots)
- Accepts: `user@.com` (starts with dot)

**Recommendation:**
Use a simple regex for better validation:

```python
import re

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def is_valid_email(email):
    """Email validation with basic regex."""
    if not email or len(email) > 254:  # RFC 5321
        return False
    return EMAIL_REGEX.match(email) is not None
```

**Effort:** 10 minutes

---

### 🟢 P2: Hardcoded Rate Limit

**Issue:** Magic link rate limit (3 per hour) is hardcoded

**Location:** `app/routes/auth.py:214`

```python
if recent_tokens['count'] >= 3:
    return False, "Too many login attempts. Please try again in an hour."
```

**Recommendation:**
Move to config:

```python
# app/config.py
MAGIC_LINK_RATE_LIMIT = int(os.getenv('MAGIC_LINK_RATE_LIMIT', '3'))
MAGIC_LINK_RATE_WINDOW = int(os.getenv('MAGIC_LINK_RATE_WINDOW', '60'))  # minutes

# app/routes/auth.py
if recent_tokens['count'] >= current_app.config['MAGIC_LINK_RATE_LIMIT']:
    window = current_app.config['MAGIC_LINK_RATE_WINDOW']
    return False, f"Too many login attempts. Please try again in {window} minutes."
```

**Effort:** 20 minutes

---

### 🟢 P2: Missing Logging for Security Events

**Issue:** Some security-sensitive actions aren't logged

**Missing logs:**
- Failed login attempts (invalid magic link)
- Admin authorization failures
- Rate limit hits

**Recommendation:**
Add security logging:

```python
# decorators.py:35
if user['email'] not in current_app.config['ADMIN_EMAILS']:
    logger.warning(f"Unauthorized admin access attempt by {user['email']}")
    abort(403)

# auth.py:214
if recent_tokens['count'] >= 3:
    logger.warning(f"Rate limit hit for user {user['email']}: {recent_tokens['count']} tokens in 1 hour")
    return False, "Too many login attempts..."
```

**Effort:** 30 minutes

---

## UX Issues

### 🟢 P2: No Loading States in Forms

**Issue:** No visual feedback when submitting forms (especially bulk import)

**Affected:**
- Bulk medal import (could take 1-2 seconds with many countries)
- Draft submission
- Admin forms

**Recommendation:**
Add loading indicators with Alpine.js or vanilla JS:

```html
<!-- Example for bulk import -->
<form x-data="{ loading: false }" @submit="loading = true">
    <!-- ... form fields ... -->
    <button type="submit" :disabled="loading">
        <span x-show="!loading">Import Medal Data</span>
        <span x-show="loading">Importing...</span>
    </button>
</form>
```

**Effort:** 1 hour for all forms

---

### 🟢 P2: Type-to-Search Hijacks All Keypresses

**Issue:** Medal table type-to-search captures ALL letter keys, even when user might want to use browser search (Ctrl+F)

**Location:** `app/templates/admin/medals.html:190-224`

```javascript
document.addEventListener('keydown', function(e) {
    // Ignore if user is typing in an input field
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return;
    }

    // Ignore special keys (except backspace)
    if (e.ctrlKey || e.metaKey || e.altKey) {  // ✅ This is good!
        return;
    }

    // Handle regular characters
    if (e.key.length === 1 && /[a-zA-Z ]/.test(e.key)) {
        e.preventDefault();  // ❌ This prevents browser search
        // ...
    }
});
```

**Impact:** Users can't use Ctrl+F / Cmd+F browser search on the page.

**Fix:** The code already checks for modifier keys, so Ctrl+F should work. **Test this to confirm.**

If it's an issue, add explicit check:
```javascript
// Don't intercept Ctrl+F / Cmd+F
if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
    return;
}
```

**Effort:** 15 minutes (testing + potential fix)

---

### 🟢 P2: Flash Messages Don't Auto-Dismiss

**Issue:** Success/info messages stay on screen until manually dismissed

**Recommendation:**
Add auto-dismiss with fade-out:

```javascript
// In base.html
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-message.success, .flash-message.info');
    flashMessages.forEach(msg => {
        setTimeout(() => {
            msg.style.transition = 'opacity 0.5s';
            msg.style.opacity = '0';
            setTimeout(() => msg.remove(), 500);
        }, 5000);  // Auto-dismiss after 5 seconds
    });
});
```

**Effort:** 30 minutes

---

## Documentation Issues

### 🟢 P2: Missing Environment Variable Documentation

**Issue:** `NO_EMAIL_MODE` and other env vars not documented in README

**Recommendation:**
Add `.env.example` with all variables:

```bash
# .env.example
# Flask
FLASK_SECRET_KEY=your-secret-key-here
FLASK_ENV=development
BASE_URL=http://localhost:5000

# Admin
ADMIN_EMAILS=admin@example.com

# Email
RESEND_API_KEY=re_xxxxxxxxxxxxxxxx
FROM_EMAIL=Olympic Medal Pool <noreply@yourdomain.com>
NO_EMAIL_MODE=true

# Session Security (set to true in production)
SESSION_COOKIE_SECURE=false

# Rate Limiting
MAGIC_LINK_RATE_LIMIT=3
MAGIC_LINK_RATE_WINDOW=60
```

**Effort:** 15 minutes

---

## Testing Gaps

### 🟢 P2: No Tests Exist

**Current State:** `tests/` directory exists but is empty.

**Recommendation:**
Add basic tests for critical paths:

1. **Auth tests:** Magic link creation, expiration, single-use
2. **Draft validation:** Budget limits, country count, duplicates
3. **Admin tests:** Medal updates, bulk import
4. **Security tests:** CSRF protection (after implementing)

**Priority tests to add first:**
```python
# tests/test_auth.py
def test_magic_link_expires()
def test_magic_link_single_use()
def test_rate_limiting()

# tests/test_draft.py
def test_budget_validation()
def test_max_countries_validation()
def test_duplicate_countries()

# tests/test_admin.py
def test_bulk_import_validation()
def test_negative_medal_count()
```

**Effort:** 4-6 hours for basic coverage

---

## Summary of Recommendations

### Immediate Actions (This Week)

1. **🔴 P0: Add CSRF Protection** (2-3 hours)
   - Install Flask-WTF
   - Add `{{ csrf_token() }}` to all POST forms
   - Test all forms still work

2. **🟡 P1: Fix Context Processor Performance** (30 min)
   - Only query user if session exists

3. **🟡 P1: Secure Session Cookies in Production** (15 min)
   - Set `SESSION_COOKIE_SECURE=true` in Railway

4. **🟡 P1: Validate SECRET_KEY in Production** (15 min)
   - Fail if not set in production

### Short-Term (Next 2 Weeks)

5. **🟢 P2: Add Input Validation** (30 min)
   - Negative medal counts
   - Better email regex

6. **🟢 P2: Add Security Logging** (30 min)
   - Failed auth attempts
   - Rate limit hits
   - Admin access denials

7. **🟢 P2: UX Improvements** (2 hours)
   - Loading states on forms
   - Auto-dismiss flash messages

8. **🟢 P2: Documentation** (15 min)
   - Create `.env.example`

### Medium-Term (Next Month)

9. **🟢 P2: Add Tests** (4-6 hours)
   - Focus on auth, validation, admin functions

10. **🟢 P2: Code Quality** (1 hour)
    - Specific exception handling
    - Move rate limits to config

---

## Positive Findings ✅

**What's working well:**

1. ✅ **SQL injection prevention** - Excellent use of parameterized queries
2. ✅ **N+1 query prevention** - Leaderboard optimized with bulk fetching
3. ✅ **Account enumeration prevention** - Consistent messages for login/register
4. ✅ **Token security** - SHA-256 hashing, single-use, expiration
5. ✅ **Transaction safety** - Proper BEGIN/COMMIT/ROLLBACK patterns
6. ✅ **Foreign key enforcement** - Enabled in SQLite
7. ✅ **Rate limiting** - Magic links limited to 3/hour
8. ✅ **Clean architecture** - Good separation of routes, decorators, db
9. ✅ **Error handling** - Good use of try/except with rollback
10. ✅ **Security mindset** - Session config, HTTPOnly cookies

---

## Metrics

- **Total Lines of Code:** 1,354
- **Critical Issues:** 1 (CSRF)
- **High Priority:** 2 (Performance, Session Security)
- **Moderate Priority:** 9 (Quality, UX, Testing)
- **Total Issues:** 12
- **Estimated Fix Time:** 12-15 hours total

---

## Next Steps

1. Review this document with the team
2. Prioritize fixes based on deployment timeline
3. Create GitHub issues for each P0/P1 item
4. Address CSRF before next deployment
5. Set up CI/CD with basic tests

---

**Reviewer:** Claude Sonnet 4.5
**Date:** January 14, 2026
**Commit:** fa1c47a
