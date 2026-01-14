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
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Auto-incrementing integer (simpler for single-instance SQLite)
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
CREATE INDEX idx_tokens_user_created ON tokens(user_id, created_at);  -- Compound index for rate limiting
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
- `/leaderboard` is visible in `open`, `locked`, and `complete` states (not `setup`)
  - In `open` state: Shows team names only, everyone tied at rank #1, no flags/medals displayed
  - In `locked`/`complete` states: Shows full leaderboard with flags, medals, and calculated ranks
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
| GET | `/leaderboard` | No | Page | Public leaderboard (visible in `open`, `locked`, `complete`) |
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

### SQL Query with Sortable Columns

```sql
-- Base query structure (ORDER BY is dynamic based on sort parameters)
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
ORDER BY {order_clause}
```

**ORDER BY clause construction:**
- Query parameters: `?sort=<column>&order=<asc|desc>`
- Valid sort columns: `points`, `gold`, `silver`, `bronze`, `team_name`
- Default: `sort=points&order=desc`

**Important: F-string usage for ORDER BY is safe ONLY when:**
- `sort_by` is validated against whitelist
- `sort_order` is validated against ('asc', 'desc')
- Actual column names are dynamic, user data is parameterized

```python
# Example ORDER BY construction
valid_sorts = ['points', 'gold', 'silver', 'bronze', 'team_name']
if sort_by not in valid_sorts:
    sort_by = 'points'
if sort_order not in ('asc', 'desc'):
    sort_order = 'desc'

if sort_order == 'desc':
    order_clause = f'''
        total_{sort_by} DESC,
        total_points DESC,
        total_gold DESC,
        total_silver DESC,
        total_bronze DESC,
        u.team_name ASC
    '''
```

### Rank Calculation

**Ranks are ALWAYS based on points tiebreaker rules, regardless of display sort order.**

Tiebreaker order for rank:
1. Total points (desc)
2. Gold medals (desc)
3. Silver medals (desc)
4. Bronze medals (desc)

**Implementation pattern:**
1. Execute SQL query with user-selected sort order
2. Calculate ranks in Python using points-based sort (ignoring display order)
3. Store ranks in `rank_map` dictionary
4. Apply ranks to teams after SQL sort

```python
# Pre-calculate ranks based on points tiebreaker
teams_for_ranking = sorted(
    [dict(t) for t in teams],
    key=lambda x: (x['total_points'], x['total_gold'], x['total_silver'], x['total_bronze']),
    reverse=True
)

rank_map = {}
current_rank = 1
prev_scores = None

for i, team in enumerate(teams_for_ranking):
    current_scores = (team['total_points'], team['total_gold'], team['total_silver'], team['total_bronze'])

    if prev_scores is not None and current_scores != prev_scores:
        current_rank = i + 1

    rank_map[team['id']] = current_rank
    prev_scores = current_scores

# Apply ranks to SQL-sorted teams
for team in teams_list:
    team['rank'] = rank_map[team['id']]
```

**Display order tiebreaker:**
- `u.team_name ASC` is always the LAST item in ORDER BY
- This ensures stable sort for tied teams
- team_name affects display order but NOT rank

**If still tied after all tiebreakers, teams share the same rank.** Display tied teams at the same position (e.g., two teams at #3, next team is #5).

### Performance Optimization: Avoiding N+1 Queries

**Problem:** Fetching countries for each team in a loop creates N+1 queries:
```python
# ❌ WRONG - N+1 query problem
for team in teams:
    countries = db.execute('''
        SELECT c.code, c.iso_code, c.name
        FROM picks p
        JOIN countries c ON p.country_code = c.code
        WHERE p.user_id = ?
    ''', [team['id']]).fetchall()
    team['countries'] = countries  # 50 teams = 50 queries!
```

**Solution:** Fetch all countries in single query, group in Python:
```python
# ✅ CORRECT - Single query for all teams
user_ids = [team['id'] for team in teams]
if user_ids:
    placeholders = ','.join('?' * len(user_ids))
    all_countries = db.execute(f'''
        SELECT p.user_id, c.code, c.iso_code, c.name
        FROM picks p
        JOIN countries c ON p.country_code = c.code
        WHERE p.user_id IN ({placeholders})
        ORDER BY p.user_id, c.name
    ''', user_ids).fetchall()

    # Group countries by user_id in Python
    countries_by_user = {}
    for row in all_countries:
        user_id = row['user_id']
        if user_id not in countries_by_user:
            countries_by_user[user_id] = []
        countries_by_user[user_id].append({
            'code': row['code'],
            'iso_code': row['iso_code'],
            'name': row['name']
        })

# Now apply to teams
for team in teams_list:
    team['countries'] = countries_by_user.get(team['id'], [])
```

**Result:** 50 teams with picks: 51 queries → 3 queries (~80% reduction)

### Flag Image Performance

**Problem:** Country flag tooltips are slow to display on hover.

**Solution - Multi-layer approach:**

1. **DNS preconnect in base.html:**
```html
<link rel="preconnect" href="https://flagcdn.com">
<link rel="dns-prefetch" href="https://flagcdn.com">
```

2. **Eager loading:**
```html
<img src="https://flagcdn.com/w40/{{ country.iso_code|lower }}.png"
     loading="eager"
     class="w-6 h-4 object-cover">
```

3. **Hardware acceleration CSS:**
```css
.flag-container img {
    will-change: transform;
    backface-visibility: hidden;
}
```

4. **JavaScript preload (locked/complete states only):**
```javascript
document.addEventListener('DOMContentLoaded', function() {
    const flagImages = document.querySelectorAll('.flag-container img');
    flagImages.forEach(img => {
        const preloadImg = new Image();
        preloadImg.src = img.src;  // Force browser cache
    });
});
```

**Note:** Browser caching handles subsequent page loads automatically.

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

## Common Pitfalls & Solutions

This section documents issues encountered during implementation and their solutions. **Read this before implementing to avoid these mistakes.**

### 0. N+1 Query Problem (CRITICAL Performance Issue)

**Problem:** Fetching related data in loops creates one query per iteration.

```python
# ❌ WRONG - For 50 teams, this executes 51 queries (1 + 50)
teams = db.execute('SELECT * FROM users').fetchall()
for team in teams:
    countries = db.execute('''
        SELECT * FROM countries
        JOIN picks ON countries.code = picks.country_code
        WHERE picks.user_id = ?
    ''', [team['id']]).fetchall()
```

**Solution:** Fetch all related data in single query, group in Python.

```python
# ✅ CORRECT - Only 2 queries total
teams = db.execute('SELECT * FROM users').fetchall()

# Fetch ALL countries for ALL teams at once
user_ids = [t['id'] for t in teams]
placeholders = ','.join('?' * len(user_ids))
all_countries = db.execute(f'''
    SELECT p.user_id, c.code, c.name
    FROM picks p
    JOIN countries c ON p.country_code = c.code
    WHERE p.user_id IN ({placeholders})
''', user_ids).fetchall()

# Group in Python
countries_by_user = {}
for row in all_countries:
    if row['user_id'] not in countries_by_user:
        countries_by_user[row['user_id']] = []
    countries_by_user[row['user_id']].append(row)
```

**When this matters:**
- Leaderboard (showing countries for each team)
- Admin user list (showing pick counts)
- Any list view with related data

**Performance impact:** 51 queries → 2 queries (~96% reduction for 50 teams)

### 1. SQLite Row Objects Are Not JSON Serializable

**Problem:**
```python
# ❌ WRONG - Row objects can't be converted to JSON
countries = db.execute('SELECT * FROM countries').fetchall()
return render_template('page.html', countries=countries)  # {{ countries|tojson }} will fail
```

**Error:**
```
TypeError: Object of type Row is not JSON serializable
```

**Solution:**
```python
# ✅ CORRECT - Convert Row objects to dicts first
countries_rows = db.execute('SELECT code, iso_code, name, cost FROM countries').fetchall()
countries = [dict(row) for row in countries_rows]
return render_template('page.html', countries=countries)  # {{ countries|tojson }} works
```

**When this matters:**
- Any time you pass database query results to templates that use `|tojson` filter
- Draft picker (countries data)
- Leaderboard (user rankings)
- Admin panels (country lists, medal data)

---

### 2. Alpine.js Script Placement and Initialization

**Problem:**
```html
<!-- ❌ WRONG - Script defined AFTER x-data tries to use it -->
<div x-data="draftPicker([...], 200, 10)">
  <!-- Alpine.js tries to call draftPicker() but it doesn't exist yet! -->
</div>

<script>
function draftPicker(initialSelected, budget, maxCountries) {
  // Function defined too late
}
</script>
```

**Error:**
```
Alpine Expression Error: Unexpected token '}'
draftPicker is not defined
```

**Solution:**
```html
<!-- ✅ CORRECT - Script BEFORE x-data -->
{% block content %}
<script>
function draftPicker(initialSelected, budget, maxCountries) {
  return {
    selected: initialSelected || [],
    // ... rest of component
  }
}
</script>

<div x-data="draftPicker({{ selected_codes|tojson|safe }}, {{ budget }}, {{ max_countries }})">
  <!-- Now Alpine.js can find draftPicker() -->
</div>
{% endblock %}
```

**Critical rules:**
1. Define JavaScript functions BEFORE the HTML that uses them
2. Always use `|tojson|safe` filter when passing Python data to JavaScript
3. Never use duplicate script tags (remove any scripts at the bottom)

---

### 3. Alpine.js Scope: Server-Side Loops vs Client-Side Loops

**Problem:**
```html
<!-- ❌ WRONG - Jinja loop creates HTML outside Alpine.js scope -->
<div x-data="draftPicker()">
  {% for country in countries %}
    <div :class="{ 'selected': isSelected('{{ country.code }}') }">
      <!-- isSelected() is not defined in this scope! -->
    </div>
  {% endfor %}
</div>
```

**Error:**
```
Uncaught ReferenceError: isSelected is not defined
Uncaught ReferenceError: canAfford is not defined
```

**Solution:**
```html
<!-- ✅ CORRECT - Alpine.js loop keeps everything in scope -->
<div x-data="draftPicker()">
  <template x-for="country in countries" :key="country.code">
    <div :class="{ 'selected': isSelected(country.code) }">
      <!-- isSelected() is accessible because we're inside Alpine.js scope -->
      <span x-text="country.name"></span>
      <span x-text="country.cost"></span>
    </div>
  </template>
</div>
```

**When to use each:**
- **Jinja loops `{% for %}`**: Use for static content that doesn't need Alpine.js reactivity
- **Alpine.js loops `<template x-for>`**: Use when content needs to access Alpine.js component properties/methods

**For draft picker specifically:**
- Country list MUST use `<template x-for>` because cards need access to:
  - `isSelected(code)` - check if country is selected
  - `canAfford(code)` - check if user can afford it
  - `toggleCountry(code)` - handle click events
  - `getCountry(code)` - get country details

---

### 4. Browser Navigation Warnings (beforeunload)

**Problem:**
```javascript
// ❌ WRONG - Warns even when user intentionally submits form
warnIfUnsaved(event) {
  if (this.selected.length > 0) {
    event.preventDefault();
    event.returnValue = '';
  }
}
```

**Issue:** User clicks "Save Picks" and gets "Leave site? Changes may not be saved" warning.

**Solution:**
```javascript
// ✅ CORRECT - Track intentional submissions
return {
  isSubmitting: false,  // Add flag

  submitPicks() {
    if (this.canSubmit()) {
      this.isSubmitting = true;  // Set flag before submit
      document.getElementById('draft-form').submit();
    }
  },

  warnIfUnsaved(event) {
    if (this.isSubmitting) return;  // Don't warn if submitting
    if (this.selected.length > 0) {
      event.preventDefault();
      event.returnValue = '';
    }
  }
}
```

---

### 5. Preserving User Selections When Editing

**Problem:** User saves picks, clicks "Edit Picks", but form shows empty (no countries selected).

**Root causes:**
1. Not passing existing picks to template
2. Not initializing Alpine.js component with existing selections
3. Scope issues preventing Alpine.js from seeing selections

**Solution:**
```python
# ✅ Backend: Fetch existing picks
@app.route('/draft')
@login_required
@require_state('open')
def draft():
    user = get_current_user()

    # Get user's current picks
    existing_picks = db.execute('''
        SELECT country_code FROM picks WHERE user_id = ?
    ''', [user['id']]).fetchall()

    selected_codes = [p['country_code'] for p in existing_picks]

    return render_template('draft/picker.html',
                         countries=countries,
                         selected_codes=selected_codes,  # Pass to template
                         budget=200,
                         max_countries=10)
```

```html
<!-- ✅ Frontend: Initialize Alpine.js with existing selections -->
<script>
function draftPicker(initialSelected, budget, maxCountries) {
  return {
    selected: initialSelected || [],  // Use initialSelected from server
    // ...
  }
}
</script>

<div x-data="draftPicker({{ selected_codes|tojson|safe }}, {{ budget }}, {{ max_countries }})">
  <!-- Component now starts with existing selections -->
</div>
```

---

### 6. Flask Auto-Reload During Development

**Problem:** Making code changes but Flask doesn't pick them up; have to manually restart server.

**Solution:**
```bash
# In .env file
FLASK_DEBUG=True
```

Or when running Flask:
```bash
flask run --debug
```

**Benefits:**
- Auto-reloads on code changes
- Better error pages with stack traces
- Debug toolbar (optional)

**Important:** Never set `FLASK_DEBUG=True` in production!

---

### 7. Atomic Database Operations for Picks

**Problem:** User's picks get partially saved if an error occurs mid-save.

**Solution:**
```python
# ✅ CORRECT - Use transactions
try:
    db.execute('BEGIN')

    # Delete existing picks
    db.execute('DELETE FROM picks WHERE user_id = ?', [user['id']])

    # Insert new picks
    for code in country_codes:
        db.execute('INSERT INTO picks (user_id, country_code) VALUES (?, ?)',
                   [user['id'], code])

    db.commit()  # All or nothing
except sqlite3.Error as e:
    db.rollback()  # Undo everything on error
    logger.error(f"Failed to save picks: {e}")
    flash('Failed to save picks. Please try again.', 'error')
```

**Why this matters:**
- Ensures data integrity
- User never ends up with half-saved picks
- Failed saves leave database in previous state

---

### 8. Server-Side Validation with Dynamic SQL

**Problem:** Need to validate budget for variable number of countries.

**Solution:**
```python
# ✅ CORRECT - Build placeholders for parameterized query
def validate_picks(country_codes):
    if len(country_codes) > 0:
        placeholders = ','.join('?' * len(country_codes))
        result = db.execute(
            f'SELECT SUM(cost) as total FROM countries WHERE code IN ({placeholders})',
            country_codes
        ).fetchone()

        total_cost = result['total'] or 0

        if total_cost > budget:
            return False, f"Total cost ({total_cost}) exceeds budget ({budget})."

    return True, None
```

**Why f-string is OK here:**
- Building `(?, ?, ?)` placeholders, NOT inserting user data
- Actual values still passed via parameterized query (second argument)
- Safe from SQL injection

**Never do:**
```python
# ❌ WRONG - SQL injection vulnerability
query = f"SELECT * FROM countries WHERE code IN ({','.join(country_codes)})"
db.execute(query)  # Dangerous!
```

---

### 9. Jinja Template Filters for Safety

**Always use `|safe` with `|tojson` when passing data to JavaScript:**

```html
<!-- ✅ CORRECT -->
<script>
const data = {{ my_data|tojson|safe }};
</script>

<div x-data="component({{ selected|tojson|safe }})">
```

**Without `|safe`, Jinja escapes the JSON:**
```html
<!-- ❌ WRONG - Jinja escapes quotes -->
<script>
const data = {{ my_data|tojson }};
// Renders as: const data = {&quot;key&quot;: &quot;value&quot;};
// JavaScript can't parse this!
</script>
```

**When to use:**
- Passing Python dicts/lists to JavaScript
- Alpine.js component initialization
- Inline JSON data in templates

---

### 10. Magic Link Implementation Details

**Must-have features:**
1. **Single-use tokens:** Set `used_at` timestamp when consumed
2. **Expiration:** Check `expires_at > CURRENT_TIMESTAMP`
3. **No account existence disclosure:** Same message for existing/new emails

```python
# ✅ CORRECT - Complete magic link verification
@app.route('/auth/<token>')
def verify_magic_link(token):
    db = get_db()

    # Check token validity
    link = db.execute('''
        SELECT * FROM tokens
        WHERE token = ?
          AND token_type = 'magic_link'
          AND used_at IS NULL
          AND expires_at > CURRENT_TIMESTAMP
    ''', [token]).fetchone()

    if not link:
        flash('Invalid or expired link. Please request a new one.', 'error')
        return redirect(url_for('login'))

    # Mark as used (single-use)
    db.execute('UPDATE tokens SET used_at = CURRENT_TIMESTAMP WHERE token = ?', [token])

    # Get or create user
    user = db.execute('SELECT * FROM users WHERE email = ?', [link['email']]).fetchone()

    # Set session
    session.permanent = True
    session['user_id'] = user['id']
    db.commit()

    return redirect(url_for('draft'))
```

---

### 11. Admin Email Configuration

**Problem:** Forgetting to set admin emails means no admin access.

**Solution:**
```bash
# .env file
ADMIN_EMAILS=your@email.com,another@email.com
```

```python
# decorators.py
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            abort(401)

        admin_emails = current_app.config.get('ADMIN_EMAILS', '').split(',')
        if user['email'] not in admin_emails:
            abort(403)

        return f(*args, **kwargs)
    return decorated_function
```

**Testing:** Use the email you registered with as an admin email in development.

---

### 12. Route Registration Pattern

**Keep it simple - register routes directly in app/__init__.py:**

```python
# ✅ CORRECT - Direct registration
from app.routes import auth, draft, leaderboard, admin

def create_app():
    app = Flask(__name__)

    # Register routes
    auth.register_routes(app)
    draft.register_routes(app)
    leaderboard.register_routes(app)
    admin.register_routes(app)

    return app
```

**Each route file:**
```python
# app/routes/draft.py
def register_routes(app):

    @app.route('/draft')
    @login_required
    @require_state('open')
    def draft():
        # ...

    @app.route('/draft/submit', methods=['POST'])
    @login_required
    @require_state('open')
    def submit_draft():
        # ...
```

**Don't use blueprints** - they add unnecessary complexity for this small app.

---

## Implementation Checklist

When implementing each feature, verify:

**Draft Picker:**
- [ ] Convert SQLite Row objects to dicts before passing to template
- [ ] Place `<script>` tag BEFORE `<div x-data>`
- [ ] Use `<template x-for>` for country cards (not Jinja `{% for %}`)
- [ ] Initialize Alpine.js component with `{{ selected_codes|tojson|safe }}`
- [ ] Add `isSubmitting` flag to prevent false navigation warnings
- [ ] Use atomic transactions (BEGIN/COMMIT) when saving picks
- [ ] Validate picks server-side with dynamic placeholders
- [ ] Fetch and pass existing picks when rendering edit form

**Magic Links:**
- [ ] Check token is unused (`used_at IS NULL`)
- [ ] Check token hasn't expired (`expires_at > CURRENT_TIMESTAMP`)
- [ ] Mark token as used after verification
- [ ] Set `session.permanent = True` for persistent login
- [ ] Don't reveal account existence (same message for all emails)

**Database Operations:**
- [ ] Always use parameterized queries (never f-strings with user data)
- [ ] Use transactions for multi-step operations
- [ ] Convert Row objects to dicts for JSON serialization
- [ ] Handle rollback on errors

**Templates:**
- [ ] Use `|tojson|safe` when passing data to JavaScript
- [ ] Place JavaScript before HTML that uses it
- [ ] Use Alpine.js loops when accessing component scope
- [ ] Use Jinja loops for static content only

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
- [ ] Leaderboard columns are sortable (desktop)
- [ ] Rank stays with team regardless of sort column
- [ ] Country flags display next to team names
- [ ] Flags support two-row layout for 5+ countries
- [ ] Flag hover shows country name instantly
- [ ] Current user's row is highlighted
- [ ] Last updated timestamp shows when medals were updated
- [ ] No N+1 query problems (check query count for 50 teams)

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
- [ ] Leaderboard hidden in 'setup' state only
- [ ] Leaderboard shows team names only in 'open' state (everyone rank #1)
- [ ] Leaderboard shows full data in 'locked' and 'complete' states
- [ ] Draft submission blocked in 'locked' and 'complete' states
- [ ] Medal entry only allowed in 'locked' and 'complete' states

**UX Polish:**
- [ ] Loading indicators visible during HTMX requests
- [ ] Flash messages display for completed actions
- [ ] Empty states have helpful messages (no picks yet, leaderboard coming soon)
- [ ] Error messages are friendly, not technical
- [ ] Unsaved draft shows warning before leaving page
