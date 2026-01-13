# CLAUDE.md - Olympic Medal Pool Project

This file is the **authoritative implementation guide** for Claude Code. Follow it exactly.


## Project Overview

A fantasy-sports-style web application for predicting Olympic medal outcomes. Users draft countries within a budget and earn points based on actual medal results during Milano Cortina 2026 (Feb 6-22, 2026).

## Hard Rules (Must Follow)

1. **Stack**: Flask + Jinja templates + HTMX + Alpine.js (draft picker only)
2. **Database**: SQLite via Python's built-in `sqlite3`. **No ORM.**
3. **Database file**: `instance/medal_pool.db`
4. **Schema source of truth**: `schema.sql` (see below)
5. **Country data source of truth**: `countries.sql`
6. **All queries**: Raw SQL with parameterized queries. Never use f-strings for SQL.
7. **Timestamps**: UTC, stored as SQLite `TIMESTAMP` or ISO8601 strings
8. **No background job frameworks**: Medal refresh (Phase 2) uses simple thread on request
9. **Minimal JS**: Alpine.js only for draft picker client state; everything else server-rendered
10. Implementation simplicity is required. Use Flask, Jinja templates, HTMX, and SQLite with direct SQL only. Do not introduce ORMs, migration frameworks, background workers, repositories, services, or layered abstractions.
11. Database schema is fixed and authoritative.
The structure defined in schema.sql must be implemented exactly. Do not add, remove, rename, or reinterpret tables, columns, constraints, or indexes unless explicitly instructed.
12. Choose the least complex valid solution.
When multiple implementations satisfy the requirements, select the one with the fewest files, the least indirection, and the smallest conceptual surface area. Avoid speculative extensibility or future-proofing.
13. Code generation scope is limited.
Generate or modify application code only within the /app directory. Treat all PRD and documentation files, including CLAUDE.md, as read-only source material.

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Flask 3.x (Python 3.11+) |
| Templates | Jinja2 |
| Interactivity | HTMX (server-driven) + Alpine.js (draft picker only) |
| Database | SQLite (direct `sqlite3`, no ORM) |
| CSS | Tailwind CSS via CDN |
| Email | Resend API (console fallback in dev) |
| Hosting | Railway |

---

## Database Schema (Authoritative)

This is the complete schema. Copy this exactly to `schema.sql`.

```sql
-- ============================================================================
-- OLYMPIC MEDAL POOL - DATABASE SCHEMA
-- ============================================================================

-- Contest configuration (single row)
CREATE TABLE contest (
    id INTEGER PRIMARY KEY CHECK (id = 1),  -- Enforce single row
    name TEXT NOT NULL DEFAULT 'Milano Cortina 2026',
    state TEXT NOT NULL DEFAULT 'setup' CHECK (state IN ('setup', 'open', 'locked', 'complete')),
    budget INTEGER NOT NULL DEFAULT 200,
    max_countries INTEGER NOT NULL DEFAULT 10,
    deadline TEXT NOT NULL,  -- ISO8601 UTC timestamp
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Users
CREATE TABLE users (
    id TEXT PRIMARY KEY,  -- UUID
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    team_name TEXT NOT NULL,  -- User's fantasy team name
    is_admin INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Countries (reference data, pre-populated from countries.sql)
CREATE TABLE countries (
    code TEXT PRIMARY KEY,  -- IOC 3-letter code (NOR, GER, SUI)
    iso_code TEXT NOT NULL,  -- ISO 2-letter code (NO, DE, CH) for flag URLs
    name TEXT NOT NULL,
    expected_points INTEGER NOT NULL,  -- Projected points (reference only)
    cost INTEGER NOT NULL,  -- Draft cost
    is_active INTEGER NOT NULL DEFAULT 1
);

-- User picks
CREATE TABLE picks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    country_code TEXT NOT NULL REFERENCES countries(code),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, country_code)
);

-- Actual medals (updated during Games)
CREATE TABLE medals (
    country_code TEXT PRIMARY KEY REFERENCES countries(code),
    gold INTEGER NOT NULL DEFAULT 0,
    silver INTEGER NOT NULL DEFAULT 0,
    bronze INTEGER NOT NULL DEFAULT 0,
    points INTEGER NOT NULL DEFAULT 0,  -- Calculated: gold*3 + silver*2 + bronze
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Auth tokens (magic links only - sessions use Flask's built-in session)
CREATE TABLE tokens (
    token TEXT PRIMARY KEY,  -- secrets.token_urlsafe(32)
    email TEXT NOT NULL,  -- Email this token is for
    token_type TEXT NOT NULL DEFAULT 'magic_link' CHECK (token_type = 'magic_link'),
    expires_at TEXT NOT NULL,  -- ISO8601 UTC
    used_at TEXT,  -- Set when consumed (single-use)
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- System metadata (key-value store for refresh timestamps, etc.)
CREATE TABLE system_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_picks_user ON picks(user_id);
CREATE INDEX idx_tokens_email ON tokens(email);
CREATE INDEX idx_tokens_expires ON tokens(expires_at);

-- Initialize contest with default values
INSERT INTO contest (id, name, state, budget, max_countries, deadline)
VALUES (1, 'Milano Cortina 2026', 'setup', 200, 10, '2026-02-04T23:59:59Z');
```

---

## Contest State Machine

| State | Description | Allowed Actions |
|-------|-------------|-----------------|
| `setup` | Admin configuring contest | Admin: edit config, import countries. Users: see "coming soon" |
| `open` | Registration and drafting open | Users: register, login, create/edit picks. Admin: all |
| `locked` | Deadline passed, Games in progress | Users: view leaderboard, view own picks (read-only). Admin: enter medals |
| `complete` | Games finished, final standings | All read-only. Leaderboard shows final results |

**Enforcement rules:**
- `POST /draft/submit` returns 403 if state != `open`
- `POST /draft/pick` returns 403 if state != `open`
- `/leaderboard` returns 404 or redirect if state == `setup`
- `/admin/medals` only accessible if state IN (`locked`, `complete`)
- State transitions: `setup` → `open` → `locked` → `complete` (no skipping, no going back)

---

## Route Contract

| Method | Path | Auth | Returns | Description |
|--------|------|------|---------|-------------|
| GET | `/` | No | Page | Home - shows CTA based on contest state |
| GET | `/register` | No | Page | Registration form |
| POST | `/register` | No | Redirect | Create user + send magic link |
| GET | `/login` | No | Page | Login form (request magic link) |
| POST | `/login` | No | Redirect | Send magic link to existing user |
| GET | `/auth/<token>` | No | Redirect | Consume magic link, set session, redirect to `/draft` or `/` |
| GET | `/logout` | Yes | Redirect | Clear session, redirect to `/` |
| GET | `/draft` | Yes | Page | Draft picker (state must be `open`) |
| POST | `/draft/toggle` | Yes | Fragment | HTMX: toggle country selection, return updated picker state |
| POST | `/draft/submit` | Yes | Redirect | Submit final picks (state must be `open`) |
| GET | `/leaderboard` | No | Page | Public leaderboard (state must be `locked` or `complete`) |
| GET | `/team/<user_id>` | No | Page | View user's picks and points breakdown |
| GET | `/my-picks` | Yes | Page | Current user's picks (read-only if locked) |
| GET | `/admin` | Admin | Page | Admin dashboard |
| GET | `/admin/contest` | Admin | Page | Edit contest config |
| POST | `/admin/contest` | Admin | Redirect | Update contest config |
| GET | `/admin/countries` | Admin | Page | Country list + import form |
| POST | `/admin/countries/import` | Admin | Redirect | Import countries from CSV |
| GET | `/admin/medals` | Admin | Page | Medal entry form |
| POST | `/admin/medals` | Admin | Redirect | Update medal counts |
| GET | `/admin/users` | Admin | Page | User list |

**Fragment vs Page:**
- Routes returning **Page** render `base.html` with full HTML document
- Routes returning **Fragment** return partial HTML for HTMX swap (no `<html>`, `<head>`, `<body>`)

---

## Template Inventory

```
app/templates/
├── base.html                    # Base layout with nav, HTMX/Alpine includes
├── index.html                   # Home page (contest state-aware)
├── auth/
│   ├── register.html            # Registration form
│   ├── login.html               # Login form
│   └── check_email.html         # "Check your email" confirmation
├── draft/
│   ├── picker.html              # Full draft page with Alpine.js state
│   ├── _country_card.html       # Fragment: single country card
│   ├── _selected_list.html      # Fragment: selected countries summary
│   └── _budget_bar.html         # Fragment: remaining budget display
├── leaderboard/
│   ├── index.html               # Main leaderboard
│   └── team.html                # Single team detail view
├── admin/
│   ├── index.html               # Admin dashboard
│   ├── contest.html             # Contest config form
│   ├── countries.html           # Country list + import
│   ├── medals.html              # Medal entry form
│   └── users.html               # User list
└── email/
    ├── magic_link.html          # Magic link email body
    └── picks_confirmed.html     # Picks confirmation email body
```

---

## Validation Rules (Server-Side)

All validation happens server-side. Alpine.js provides UX hints only.

### Draft Submission
```python
def validate_picks(user_id, country_codes):
    db = get_db()
    contest = db.execute('SELECT budget, max_countries, state FROM contest WHERE id = 1').fetchone()
    
    # Check contest state
    if contest['state'] != 'open':
        return False, "Contest is not open for picks"
    
    # Check count
    if len(country_codes) > contest['max_countries']:
        return False, f"Maximum {contest['max_countries']} countries allowed"
    
    if len(country_codes) == 0:
        return False, "Must select at least one country"
    
    # Check budget
    placeholders = ','.join('?' * len(country_codes))
    total_cost = db.execute(
        f'SELECT SUM(cost) as total FROM countries WHERE code IN ({placeholders})',
        country_codes
    ).fetchone()['total']
    
    if total_cost > contest['budget']:
        return False, f"Total cost {total_cost} exceeds budget {contest['budget']}"
    
    # Check duplicates
    if len(country_codes) != len(set(country_codes)):
        return False, "Duplicate countries not allowed"
    
    return True, None
```

### Magic Link
- Token expires after 15 minutes
- Token is single-use (set `used_at` on consumption)
- If user doesn't exist, create on first click

### Session (Simplified)
Use Flask's built-in session. No separate session tokens table needed.

```python
# config.py
from datetime import timedelta

PERMANENT_SESSION_LIFETIME = timedelta(days=21)
SESSION_COOKIE_SECURE = True  # Set False for local dev
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# In auth route after magic link verified:
@app.route('/auth/<token>')
def verify_magic_link(token):
    db = get_db()
    link = db.execute('''
        SELECT * FROM tokens 
        WHERE token = ? AND token_type = 'magic_link' 
        AND used_at IS NULL AND expires_at > CURRENT_TIMESTAMP
    ''', [token]).fetchone()
    
    if not link:
        flash('Invalid or expired link')
        return redirect(url_for('auth.login'))
    
    # Mark token as used
    db.execute('UPDATE tokens SET used_at = CURRENT_TIMESTAMP WHERE token = ?', [token])
    
    # Get or create user
    user = db.execute('SELECT * FROM users WHERE email = ?', [link['email']]).fetchone()
    if not user:
        # First login - redirect to complete registration
        session['pending_email'] = link['email']
        return redirect(url_for('auth.complete_registration'))
    
    # Set session
    session.permanent = True
    session['user_id'] = user['id']
    db.commit()
    
    return redirect(url_for('draft.picker'))
```

---

## HTMX Error Handling

For validation errors, return HTTP 422 with an error fragment. HTMX swaps the error into the page.

```python
from flask import make_response

def validation_error(message):
    """Return a 422 response with error HTML for HTMX."""
    html = f'<div class="error-message bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">{message}</div>'
    response = make_response(html, 422)
    return response

# Usage in draft route:
@app.route('/draft/submit', methods=['POST'])
@login_required
@require_state('open')
def submit_draft():
    country_codes = request.form.getlist('countries')
    valid, error = validate_picks(current_user['id'], country_codes)
    
    if not valid:
        return validation_error(error)
    
    # ... save picks ...
    return redirect(url_for('draft.confirmed'))
```

**In templates:**
```html
<!-- Error container for HTMX swaps -->
<div id="error-container"></div>

<!-- Form with HTMX error handling -->
<form hx-post="/draft/submit" 
      hx-target="#error-container" 
      hx-target-422="#error-container"
      hx-swap="innerHTML">
    ...
</form>
```

---

## Unhappy Path Flows

### Magic Link Errors

**Expired or invalid token:**
```
User clicks old/bad link → /auth/<token>
  ↓
Token not found OR expires_at < now OR used_at IS NOT NULL
  ↓
Flash message: "This link has expired or already been used."
  ↓
Redirect to /login with pre-filled email (if available)
```

**Email not delivered:**
```
User doesn't receive email → visits /login again
  ↓
Show: "Didn't get the email? Check spam, or [resend link]"
  ↓
Rate limit: max 3 magic links per email per hour
  ↓
If Resend is down: Admin can generate link manually via /admin/users
```

### Draft Validation Errors

**Budget exceeded:**
```
User submits picks totaling 210 points (budget: 200)
  ↓
Server returns HTTP 422 + error fragment
  ↓
HTMX swaps into #error-container:
  "Total cost (210) exceeds your budget of 200. Remove some countries."
  ↓
User's selections PRESERVED (no page reload, just error message)
```

**Too many countries:**
```
User submits 12 countries (max: 10)
  ↓
Server returns HTTP 422 + error fragment
  ↓
"You've selected 12 countries. Maximum allowed is 10."
  ↓
User's selections PRESERVED
```

**Deadline passed mid-draft:**
```
User loads /draft while state='open'
  ↓
Admin changes state to 'locked' while user is drafting
  ↓
User clicks Submit
  ↓
@require_state('open') returns 403
  ↓
Show: "The entry deadline has passed. Your picks were not saved."
  ↓
Link to /leaderboard
```

### Abandoned Draft

**User leaves without submitting:**
```
User selects countries but closes browser
  ↓
Selections stored in Alpine.js (client-side only)
  ↓
On return: selections are LOST (no server-side draft state)
  ↓
This is acceptable - keep it simple, no auto-save complexity
```

**UX mitigation:** Show clear "unsaved changes" warning before navigation:
```html
<div x-data="draftPicker()" @beforeunload.window="warnIfUnsaved($event)">
```

### Registration Errors

**Email already exists:**
```
User submits registration with existing email
  ↓
Don't reveal account existence (security)
  ↓
Show same message as success: "Check your email for a login link"
  ↓
Send magic link to existing user (they can just log in)
```

**Invalid email format:**
```
User enters "notanemail"
  ↓
HTML5 validation catches client-side (type="email")
  ↓
If bypassed, server returns 422: "Please enter a valid email address"
```

### Medal Data Errors

**Sports Data Hub unavailable (Phase 2):**
```
Background refresh fails (timeout, 500, etc.)
  ↓
Keep existing medal data (don't clear on failure)
  ↓
Update system_meta with last_error timestamp
  ↓
Show on leaderboard: "Medal data last updated: 2 hours ago ⚠️"
  ↓
If stale > 1 hour, show admin alert on /admin dashboard
```

**Admin enters invalid medal count:**
```
Admin submits negative number or non-integer
  ↓
Server returns 422: "Medal counts must be non-negative integers"
  ↓
Form values preserved for correction
```

---

## UX Polish Guidelines

Keep interactions fast and predictable. Users should never wonder "did that work?"

### Loading States
```html
<!-- Show spinner during HTMX requests -->
<button hx-post="/draft/submit" hx-indicator="#spinner">
  Submit Picks
  <span id="spinner" class="htmx-indicator">⏳</span>
</button>
```

### Success Feedback
```html
<!-- Flash messages for completed actions -->
{% with messages = get_flashed_messages(with_categories=true) %}
  {% for category, message in messages %}
    <div class="flash flash-{{ category }}">{{ message }}</div>
  {% endfor %}
{% endwith %}
```

### Draft Picker UX
- **Disabled states:** Grey out countries user can't afford
- **Running totals:** Always visible: "Budget: 47/200 | Countries: 3/10"
- **Selection feedback:** Immediate visual toggle (Alpine.js), no server round-trip needed
- **Submit button:** Disabled until at least 1 country selected

### Mobile Considerations
- Touch targets minimum 44x44px
- Single-column layout on mobile
- Leaderboard: horizontal scroll for medal columns if needed
- Draft picker: stack country cards vertically

### Empty States
```html
<!-- No picks yet -->
<div class="empty-state">
  <p>You haven't selected any countries yet.</p>
  <p>Tap a country below to add it to your team.</p>
</div>

<!-- Leaderboard before games start -->
<div class="empty-state">
  <p>The leaderboard will appear once the Games begin.</p>
  <p>Entry deadline: February 4, 2026</p>
</div>
```

### Error Message Tone
- ❌ "Error: Budget constraint violation"
- ✅ "You're 10 points over budget. Try removing a country."

- ❌ "403 Forbidden"  
- ✅ "The entry deadline has passed."

- ❌ "Invalid token"
- ✅ "This link has expired. Request a new one below."

---

## Admin Authorization

```python
# config.py
ADMIN_EMAILS = os.getenv('ADMIN_EMAILS', '').split(',')

# decorators.py
from functools import wraps
from flask import current_app, abort, g

def get_current_user():
    """Get current user from session."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    db = get_db()
    return db.execute('SELECT * FROM users WHERE id = ?', [user_id]).fetchone()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not get_current_user():
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            abort(401)
        if user['email'] not in current_app.config['ADMIN_EMAILS']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def require_state(*allowed_states):
    """Decorator to enforce contest state. Usage: @require_state('open')"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            db = get_db()
            contest = db.execute('SELECT state FROM contest WHERE id = 1').fetchone()
            if contest['state'] not in allowed_states:
                abort(403, f"Action not allowed in '{contest['state']}' state")
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

**Usage:**
```python
@app.route('/draft/submit', methods=['POST'])
@login_required
@require_state('open')
def submit_draft():
    # Only executes if contest.state == 'open'
    ...

@app.route('/admin/medals', methods=['POST'])
@admin_required
@require_state('locked', 'complete')
def update_medals():
    # Only executes if contest.state in ('locked', 'complete')
    ...
```

---

## Country Import Format

Admin imports countries via CSV paste. Required format:

```csv
code,iso_code,name,expected_points,cost
NOR,NO,Norway,87,98
GER,DE,Germany,64,65
USA,US,United States,58,57
```

**Rules:**
- First row must be header: `code,iso_code,name,expected_points,cost`
- `code` is 3-letter IOC code, must be unique
- `iso_code` is 2-letter ISO code for flag images
- All fields required
- Import replaces all existing countries (truncate + insert)

**Flag images:** Use `iso_code` to construct flag URLs in templates:
```html
<img src="https://flagcdn.com/w40/{{ country.iso_code|lower }}.png" alt="{{ country.name }}">
```

**Canonical data:** `countries.sql` contains the authoritative country list. Generate from `MiCo2026_Country_Pricing.xlsx`.

---

## Leaderboard Calculation

```sql
SELECT 
    u.id,
    u.name,
    u.team_name,
    COALESCE(SUM(m.gold), 0) as total_gold,
    COALESCE(SUM(m.silver), 0) as total_silver,
    COALESCE(SUM(m.bronze), 0) as total_bronze,
    COALESCE(SUM(m.points), 0) as total_points
FROM users u
JOIN picks p ON u.id = p.user_id
LEFT JOIN medals m ON p.country_code = m.country_code
GROUP BY u.id
ORDER BY 
    total_points DESC,
    total_gold DESC,
    total_silver DESC,
    total_bronze DESC
```

**Tiebreaker order:**
1. Total points (desc)
2. Gold medals (desc)
3. Silver medals (desc)
4. Bronze medals (desc)

**If still tied after all tiebreakers, teams share the same rank.** Display tied teams at the same position (e.g., two teams at #3, next team is #5).

---

## Medal Updates

When admin updates medal counts, always recalculate `points`:

```python
def update_medals(country_code, gold, silver, bronze):
    db = get_db()
    points = gold * 3 + silver * 2 + bronze
    db.execute('''
        INSERT INTO medals (country_code, gold, silver, bronze, points, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(country_code) DO UPDATE SET
            gold = excluded.gold,
            silver = excluded.silver,
            bronze = excluded.bronze,
            points = excluded.points,
            updated_at = CURRENT_TIMESTAMP
    ''', [country_code, gold, silver, bronze, points])
    db.commit()
```

**Phase 2 - Sports Data Hub refresh:** Same pattern, iterate through API response and call `update_medals()` for each country.

---

## Environment Variables

```bash
# Required
FLASK_SECRET_KEY=your-secret-key-min-32-chars
BASE_URL=http://localhost:5000

# Required for production
RESEND_API_KEY=re_xxxxxxxx

# Optional
ADMIN_EMAILS=admin1@example.com,admin2@example.com

# Phase 2 - Sports Data Hub
SPORTS_DATA_HUB_URL=https://api.example.com/medals
SPORTS_DATA_HUB_API_KEY=your-api-key
MEDAL_REFRESH_MINUTES=15
```

**Minimal `.env` for local development:**
```bash
FLASK_SECRET_KEY=dev-secret-key-for-local-testing-only
BASE_URL=http://localhost:5000
ADMIN_EMAILS=your@email.com
```

---

## Email Handling

```python
# services/email.py
import resend
from flask import current_app, render_template

def send_email(to, subject, template, **kwargs):
    html = render_template(f'email/{template}', **kwargs)
    
    if not current_app.config.get('RESEND_API_KEY'):
        # Dev mode - print to console
        print(f"\n{'='*60}")
        print(f"TO: {to}")
        print(f"SUBJECT: {subject}")
        print(f"{'='*60}")
        print(html)
        print(f"{'='*60}\n")
        return True
    
    resend.api_key = current_app.config['RESEND_API_KEY']
    resend.Emails.send({
        "from": "Olympic Medal Pool <noreply@yourdomain.com>",
        "to": to,
        "subject": subject,
        "html": html
    })
    return True
```

---

## Local Development

```bash
# Setup
git clone <repo>
cd olympic-medal-pool
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize database
flask init-db

# Run
flask run
# App at http://localhost:5000
```

**Requirements (requirements.txt):**
```
flask>=3.0
gunicorn>=21.0
python-dotenv>=1.0
resend>=0.7
requests>=2.31
```

---

## Project Structure

```
olympic-medal-pool/
├── app/
│   ├── __init__.py              # Flask app factory, register blueprints
│   ├── config.py                # Configuration from env vars
│   ├── db.py                    # Database connection + helpers
│   ├── decorators.py            # @login_required, @admin_required
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py              # /register, /login, /auth/<token>, /logout
│   │   ├── draft.py             # /draft, /draft/toggle, /draft/submit
│   │   ├── leaderboard.py       # /leaderboard, /team/<id>, /my-picks
│   │   └── admin.py             # /admin/*
│   ├── services/
│   │   ├── __init__.py
│   │   ├── email.py             # Resend integration
│   │   └── medals.py            # Medal refresh logic (Phase 2)
│   ├── templates/               # See Template Inventory above
│   └── static/
│       └── css/
│           └── custom.css       # Any overrides to Tailwind
├── schema.sql                   # Authoritative database schema
├── countries.sql                # Authoritative country data
├── tests/
│   ├── test_auth.py
│   ├── test_draft.py
│   ├── test_leaderboard.py
│   └── test_admin.py
├── .env.example
├── requirements.txt
├── railway.toml
├── color-palette.md
└── README.md
```

---

## Deployment (Railway)

1. Connect GitHub repo to Railway
2. Set environment variables in Railway dashboard
3. Railway auto-detects Python
4. Start command: `gunicorn "app:create_app()"`

---

## Acceptance Criteria Checklist

Before considering the app complete, verify:

**Happy Paths:**
- [ ] Register flow: new user can register, receives magic link, clicks link, lands on draft page
- [ ] Login flow: existing user can request magic link, click it, session persists
- [ ] Draft picker shows all countries with costs and flags
- [ ] Leaderboard shows correct points: gold×3 + silver×2 + bronze×1
- [ ] Leaderboard tiebreakers work: points → golds → silvers → bronzes (ties allowed)
- [ ] Tied teams display at same rank (e.g., two #3s, next is #5)
- [ ] Admin can import countries from CSV
- [ ] Admin can update medal counts (points auto-calculated)
- [ ] Admin can change contest state
- [ ] Mobile leaderboard is readable and functional

**Unhappy Paths:**
- [ ] Expired magic link shows friendly error + link to request new one
- [ ] Used magic link shows friendly error (single-use enforced)
- [ ] Budget exceeded returns 422 with clear message, selections preserved
- [ ] Max countries exceeded returns 422 with clear message, selections preserved
- [ ] Submit after deadline returns friendly "deadline passed" message
- [ ] Duplicate email registration sends magic link (doesn't reveal account exists)
- [ ] Invalid email format rejected with clear message

**State Enforcement:**
- [ ] @require_state decorator blocks actions in wrong state
- [ ] Leaderboard hidden in 'setup' and 'open' states
- [ ] Draft submission blocked in 'locked' and 'complete' states
- [ ] Medal entry only allowed in 'locked' and 'complete' states

**UX Polish:**
- [ ] Loading indicators visible during HTMX requests
- [ ] Flash messages display for completed actions
- [ ] Empty states have helpful messages (no picks yet, leaderboard coming soon)
- [ ] Error messages are friendly, not technical
- [ ] Unsaved draft shows warning before leaving page
