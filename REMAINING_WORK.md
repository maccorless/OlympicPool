# Remaining Work - Olympic Medal Pool

Last Updated: January 14, 2026

---

## Current Status

✅ **Phase 1 Complete** - Core Application
- User registration & magic link authentication
- Draft picker with budget constraints
- Leaderboard with sortable columns
- Admin panel (contest config, country import, medal entry, bulk import)
- Mobile responsive design
- Type-to-search on medal entry

✅ **Recent Fixes**
- Context processor performance optimization (66% fewer queries)
- Rebranded to "XXV Winter Olympic Games"
- Added admin medal entry enhancements

---

## Critical - Before Production Launch 🔴

### 1. CSRF Protection (P0 - REQUIRED)
**Priority:** Must fix before deployment
**Effort:** 2-3 hours
**Risk:** High security vulnerability

**Tasks:**
- [ ] Install Flask-WTF: `pip install flask-wtf`
- [ ] Add CSRF initialization in `app/__init__.py`
- [ ] Add `{{ csrf_token() }}` to all 7 POST forms:
  - [ ] `/register` - `auth/register.html`
  - [ ] `/login` - `auth/login.html`
  - [ ] `/draft/submit` - `draft/picker.html`
  - [ ] `/admin/contest` - `admin/contest.html`
  - [ ] `/admin/countries/import` - `admin/countries.html`
  - [ ] `/admin/medals` - `admin/medals.html`
  - [ ] `/admin/medals/bulk` - `admin/medals_bulk.html`
- [ ] Test all forms still work
- [ ] Update `requirements.txt`

**Implementation:**
```python
# app/__init__.py
from flask_wtf.csrf import CSRFProtect

def create_app():
    app = Flask(__name__)
    # ... existing config ...

    csrf = CSRFProtect(app)

    # ... rest of setup ...
```

---

## High Priority - Pre-Launch 🟡

### 2. Production Security Configuration (P1)
**Effort:** 30 minutes
**Tasks:**
- [ ] Set `SESSION_COOKIE_SECURE=true` in Railway environment
- [ ] Add SECRET_KEY validation (fail if not set in production)
- [ ] Update `app/config.py` with production checks:

```python
import os

# Detect production
IS_PRODUCTION = os.getenv('FLASK_ENV') == 'production' or os.getenv('RAILWAY_ENVIRONMENT') is not None

# Secret key validation
SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
if not SECRET_KEY:
    if IS_PRODUCTION:
        raise RuntimeError("FLASK_SECRET_KEY must be set in production")
    SECRET_KEY = 'dev-secret-key-for-local-testing-only'

# Session security
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', str(IS_PRODUCTION)).lower() == 'true'
```

### 3. Environment Variable Documentation (P1)
**Effort:** 15 minutes
**Tasks:**
- [ ] Create `.env.example` with all required variables
- [ ] Document deployment steps in README.md
- [ ] Add Railway-specific configuration guide

---

## Medium Priority - Post-Launch Improvements 📋

### 4. Input Validation Improvements (P2)
**Effort:** 30 minutes
**Tasks:**
- [ ] Add negative medal count validation in admin routes
- [ ] Add max value validation (e.g., max 999 medals)
- [ ] Improve email validation with regex
- [ ] Add HTML validation attributes (`min="0"` `max="999"`)

### 5. Error Handling Improvements (P2)
**Effort:** 30 minutes
**Tasks:**
- [ ] Replace broad `except Exception` in bulk import with specific exceptions
- [ ] Add security event logging (failed auth, rate limits, admin denials)
- [ ] Add structured logging with log levels

### 6. UX Enhancements (P2)
**Effort:** 2 hours
**Tasks:**
- [ ] Add loading states to all forms
- [ ] Auto-dismiss flash messages after 5 seconds
- [ ] Test type-to-search doesn't block Ctrl+F
- [ ] Add keyboard shortcuts documentation

### 7. Configuration Improvements (P2)
**Effort:** 30 minutes
**Tasks:**
- [ ] Move rate limits to config (currently hardcoded at 3/hour)
- [ ] Make magic link expiration configurable
- [ ] Add config for session lifetime

---

## Testing - Critical Gap 🧪

### 8. Test Suite (P2)
**Effort:** 4-6 hours
**Priority:** Add before Phase 2

**Tasks:**
- [ ] Set up pytest framework
- [ ] Auth tests:
  - [ ] Magic link creation and expiration
  - [ ] Single-use token enforcement
  - [ ] Rate limiting (3 per hour)
  - [ ] Session persistence
- [ ] Draft validation tests:
  - [ ] Budget constraint validation
  - [ ] Max countries validation
  - [ ] Duplicate country validation
  - [ ] Invalid country codes
- [ ] Admin tests:
  - [ ] Authorization (admin emails only)
  - [ ] Medal update calculations
  - [ ] Bulk import parsing
  - [ ] Negative medal validation
- [ ] Security tests:
  - [ ] CSRF protection (after implementing)
  - [ ] SQL injection attempts
  - [ ] XSS prevention

**Test file structure:**
```
tests/
├── conftest.py          # Fixtures
├── test_auth.py         # Authentication flows
├── test_draft.py        # Draft validation
├── test_leaderboard.py  # Ranking calculations
├── test_admin.py        # Admin functions
└── test_security.py     # Security tests
```

---

## Future Features - Phase 2 🚀

### 9. Automated Medal Data Refresh (Phase 2)
**Status:** Not started
**Effort:** 4-6 hours
**Priority:** Low (manual entry working fine)

**Requirements from CLAUDE.md:**
- Simple thread on request (no background job frameworks)
- Fetch from Sports Data Hub API
- Update medals table
- Handle API failures gracefully
- Show "last updated" timestamp
- Alert admin if data is stale (> 1 hour)

**Tasks:**
- [ ] Research Sports Data Hub API endpoint
- [ ] Add API credentials to config
- [ ] Implement refresh logic in `app/services/medals.py`
- [ ] Add `/admin/medals/refresh` route
- [ ] Add error handling for API failures
- [ ] Update `system_meta` table with last refresh timestamp
- [ ] Add stale data warning to admin dashboard

**Environment variables needed:**
```bash
SPORTS_DATA_HUB_URL=https://api.example.com/medals
SPORTS_DATA_HUB_API_KEY=your-api-key
MEDAL_REFRESH_MINUTES=15
```

### 10. Additional Nice-to-Haves (Future)
**Priority:** Optional enhancements

- [ ] Email confirmations when picks are submitted
- [ ] Team comparison view (compare two teams side-by-side)
- [ ] Historical stats (if running multiple years)
- [ ] Export leaderboard to CSV
- [ ] Public API for leaderboard data
- [ ] Dark mode toggle
- [ ] User profile pages
- [ ] Social sharing (share your team)

---

## Deployment Checklist ✈️

### Pre-Deployment (Before going live)
- [ ] ✅ CSRF protection implemented
- [ ] ✅ SECRET_KEY set in Railway
- [ ] ✅ SESSION_COOKIE_SECURE=true in Railway
- [ ] ✅ ADMIN_EMAILS configured
- [ ] ✅ FROM_EMAIL configured
- [ ] ✅ RESEND_API_KEY set (or NO_EMAIL_MODE=false)
- [ ] Database initialized with schema
- [ ] Countries imported from CSV
- [ ] At least basic tests passing
- [ ] .env.example created and documented

### Post-Deployment Monitoring
- [ ] Monitor error logs in Railway
- [ ] Test magic link emails work
- [ ] Test admin access works
- [ ] Test draft submission works
- [ ] Test leaderboard updates
- [ ] Monitor database size
- [ ] Monitor response times

---

## Estimated Timeline

**Pre-Launch (Critical Path):**
- CSRF Protection: 2-3 hours
- Security Config: 30 minutes
- Documentation: 15 minutes
- Testing & Validation: 1 hour
- **Total: 4-5 hours**

**Post-Launch Improvements:**
- Input Validation: 30 minutes
- Error Handling: 30 minutes
- UX Enhancements: 2 hours
- Basic Test Suite: 4-6 hours
- **Total: 7-9 hours**

**Phase 2 (Optional):**
- Medal API Integration: 4-6 hours
- **Total: 4-6 hours**

---

## Summary by Priority

| Priority | Item | Status | Effort | Blocking Launch? |
|----------|------|--------|--------|------------------|
| 🔴 P0 | CSRF Protection | ❌ Not started | 2-3 hrs | ✅ YES |
| 🟡 P1 | Context Processor Cache | ✅ Complete | - | - |
| 🟡 P1 | Session Security | ❌ Not started | 30 min | ✅ YES |
| 🟡 P1 | SECRET_KEY Validation | ❌ Not started | 15 min | ✅ YES |
| 🟡 P1 | .env.example | ❌ Not started | 15 min | ⚠️ Recommended |
| 📋 P2 | Input Validation | ❌ Not started | 30 min | ❌ No |
| 📋 P2 | Error Handling | ❌ Not started | 30 min | ❌ No |
| 📋 P2 | UX Improvements | ❌ Not started | 2 hrs | ❌ No |
| 📋 P2 | Test Suite | ❌ Not started | 4-6 hrs | ❌ No |
| 🚀 Phase 2 | Medal API | ❌ Not started | 4-6 hrs | ❌ No |

---

## Next Actions

**Immediate (This Week):**
1. Implement CSRF protection
2. Configure production security settings
3. Create .env.example
4. Deploy to Railway staging
5. Test all critical paths

**Short-term (Next 2 Weeks):**
1. Add input validation
2. Improve error handling
3. Add basic test coverage
4. Monitor production issues

**Long-term (As Needed):**
1. Consider Phase 2 medal API
2. Add nice-to-have features based on user feedback

---

**Last Review:** January 14, 2026
**Next Review:** After CSRF implementation
