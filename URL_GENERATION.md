# URL Generation Guide

This document clarifies when to use different URL generation methods in the app.

## Three Types of URLs

### 1. **Internal Navigation Links** (Relative URLs)
**Use:** `url_for()` function
**When:** Links clicked by users to navigate within the app
**Why:** Works with any domain/port automatically

```python
# Python
url_for('contest_home', event_slug='milano-2026', contest_slug='office-pool')
# Returns: /milano-2026/office-pool

# Jinja Template
<a href="{{ url_for('leaderboard', event_slug=event.slug, contest_slug=contest.slug) }}">
    Leaderboard
</a>
```

### 2. **Display URLs** (Dynamic Absolute URLs)
**Use:** `request.url_root`
**When:** Showing users a URL to copy/share (in the admin interface)
**Why:** Detects current domain/port, works in dev and production

```python
# Python (in routes)
base_url = request.url_root.rstrip('/')  # http://localhost:5001 or https://myapp.railway.app

# Jinja Template (display only, not href)
{{ base_url }}/{{ event.slug }}/{{ contest.slug }}
```

**Important:** Always use `url_for()` for the actual `href` attribute, even when displaying the full URL:

```html
<!-- ✅ CORRECT: href is relative, display text is absolute -->
<a href="{{ url_for('contest_home', event_slug=event.slug, contest_slug=contest.slug) }}">
    {{ base_url }}/{{ event.slug }}/{{ contest.slug }}
</a>

<!-- ❌ WRONG: href is hardcoded to specific port -->
<a href="{{ base_url }}/{{ event.slug }}/{{ contest.slug }}">
    {{ base_url }}/{{ event.slug }}/{{ contest.slug }}
</a>
```

### 3. **External URLs** (Configured Absolute URLs)
**Use:** `current_app.config['BASE_URL']`
**When:** URLs sent outside the app (emails, SMS)
**Why:** Configured per environment, may differ from current request (e.g., Railway app URL vs custom domain)

```python
# In email templates or SMS messages
magic_link = f"{current_app.config['BASE_URL']}/milano-2026/office-pool/login?token={token}"
```

## Configuration

### `.env` file (Development)
```bash
BASE_URL=http://localhost:5001
```

### Railway Environment Variables (Production)
```bash
BASE_URL=https://olympic-pool.railway.app
```

## Examples from Codebase

### ✅ Global Admin Dashboard (`_contest_card.html`)
```html
<!-- Clickable link uses url_for (relative) -->
<a href="{{ url_for('contest_home', event_slug=contest.event_slug, contest_slug=contest.slug) }}"
   target="_blank"
   class="text-sm text-blue-600 hover:underline">
    <!-- Display text shows full URL (request.url_root) -->
    {{ base_url }}/{{ contest.event_slug }}/{{ contest.slug }}
</a>

<!-- Copy button uses full URL -->
<button onclick="copyContestUrl('{{ base_url }}/{{ contest.event_slug }}/{{ contest.slug }}', this)">
    Copy URL
</button>
```

### ✅ Navigation Bar (`base.html`)
```html
<!-- All navigation uses url_for -->
<a href="{{ url_for('leaderboard', event_slug=event.slug, contest_slug=contest.slug) }}">
    Leaderboard
</a>
```

### ✅ Magic Link Email (future implementation)
```python
# Use config BASE_URL for external links
magic_link_url = f"{current_app.config['BASE_URL']}/{event_slug}/{contest_slug}/login?token={token}"
send_email(user.email, magic_link_url)
```

## Why This Matters

### Problem: Hardcoded Port
```python
# ❌ WRONG: Breaks when port changes
base_url = "http://localhost:5001"
href = f"{base_url}/milano-2026/office-pool"
```

If you run Flask on port 5000 instead of 5001, all links break!

### Solution: Dynamic Detection
```python
# ✅ CORRECT: Works with any port
base_url = request.url_root.rstrip('/')  # Auto-detects from current request
href = url_for('contest_home', event_slug='milano-2026', contest_slug='office-pool')
```

## Common Mistakes

### ❌ Using `BASE_URL` config for internal navigation
```html
<!-- WRONG: Hardcoded to config port -->
<a href="{{ config.BASE_URL }}/{{ event.slug }}/{{ contest.slug }}">Link</a>
```

### ❌ Using `url_for()` in emails
```python
# WRONG: Generates relative URL, won't work in email
magic_link = url_for('login', event_slug=event_slug, contest_slug=contest_slug, _external=False)
# Returns: /milano-2026/office-pool/login (no domain!)
```

### ✅ Correct email URL
```python
# CORRECT: Use _external=True or config BASE_URL
magic_link = url_for('login', event_slug=event_slug, contest_slug=contest_slug, _external=True)
# Returns: http://localhost:5001/milano-2026/office-pool/login
```

## Summary

| Use Case | Method | Example |
|----------|--------|---------|
| Navigation links | `url_for()` | `<a href="{{ url_for('leaderboard', ...) }}">` |
| Display/copy URLs | `request.url_root` | `{{ base_url }}/milano-2026/office-pool` |
| Email/SMS links | `config['BASE_URL']` or `url_for(..., _external=True)` | Magic links |

**Golden Rule:** Navigation links should ALWAYS use `url_for()` so they work regardless of domain/port.
