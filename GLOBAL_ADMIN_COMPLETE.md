# Global Admin System - Implementation Complete ✅

**Branch:** `multi`
**Status:** Fully implemented and ready for use
**Access:** `/admin/global`

---

## Overview

Implemented a separate **Global Admin** system distinct from contest-level admin, enabling future role-based access control:

- **Global Admins** - Can create/manage events and contests system-wide
- **Contest Admins** (future) - Can only manage specific contests they're assigned to

---

## What Was Implemented

### 1. Authorization System

**New Configuration (`app/config.py`):**
```python
# Contest-level admin (can manage individual contests)
ADMIN_EMAILS = [...]

# Global admin (can create events/contests, system-wide access)
GLOBAL_ADMIN_EMAILS = [...]  # Defaults to ADMIN_EMAILS if not set
```

**.env Configuration:**
```bash
# Both roles for now (can be separated later)
ADMIN_EMAILS=ken@corless.com
GLOBAL_ADMIN_EMAILS=ken@corless.com  # Optional, defaults to ADMIN_EMAILS
```

**New Decorator (`app/decorators.py`):**
```python
@global_admin_required
def my_route():
    # Only accessible to users in GLOBAL_ADMIN_EMAILS
    pass
```

### 2. Global Admin Routes (`app/routes/global_admin.py`)

**System Overview:**
- `GET /admin/global` - Dashboard with system-wide stats

**Event Management:**
- `GET /admin/global/events` - List all events
- `GET /admin/global/events/create` - Create new event form
- `POST /admin/global/events/create` - Create event
- `GET /admin/global/events/<id>/edit` - Edit event form
- `POST /admin/global/events/<id>/edit` - Update event

**Contest Management:**
- `GET /admin/global/contests` - List all contests across all events
- `GET /admin/global/contests/create` - Create new contest form
- `POST /admin/global/contests/create` - Create contest
- `GET /admin/global/contests/<id>/edit` - Edit contest form
- `POST /admin/global/contests/<id>/edit` - Update contest

### 3. Templates

**Created:**
- `app/templates/admin/global/dashboard.html` - System overview
- `app/templates/admin/global/events.html` - Events list
- `app/templates/admin/global/event_form.html` - Create/edit event
- `app/templates/admin/global/contests.html` - Contests list
- `app/templates/admin/global/contest_form.html` - Create/edit contest

**Navigation Updated (`base.html`):**
```html
<!-- Global Admin link (visible everywhere for global admins) -->
{% if session.user_id and user and user.email in config.GLOBAL_ADMIN_EMAILS %}
    <a href="{{ url_for('global_admin_dashboard') }}" class="text-red-700 hover:text-red-900 font-semibold">
        🌐 Global Admin
    </a>
{% endif %}
```

### 4. Features

**Event Management:**
- ✅ Create new Olympic Games events (e.g., "LA 2028", "Paris 2024")
- ✅ Edit event details (name, dates, description)
- ✅ Activate/deactivate events
- ✅ View event statistics (contest count, user count)

**Contest Management:**
- ✅ Create new contests within any event
- ✅ Configure contest settings (budget, max countries, deadline)
- ✅ Set contest state (setup/open/locked/complete)
- ✅ View contest statistics (users, picks)
- ✅ Quick link to contest-specific admin panel

**System Dashboard:**
- ✅ Total events count
- ✅ Total contests count
- ✅ Total users count
- ✅ Total countries count
- ✅ Recent events list with statistics
- ✅ Quick actions (create event/contest, manage events/contests)

---

## Usage Guide

### Accessing Global Admin

1. **Login** as a user with global admin privileges (ken@corless.com)
2. **Navigate** to any page - you'll see "🌐 Global Admin" in the top navigation
3. **Click** the Global Admin link to access the dashboard

**Direct URL:** `http://localhost:5002/admin/global`

### Creating a New Event

1. Visit `/admin/global` or `/admin/global/events`
2. Click "➕ Create Event"
3. Fill out the form:
   - **Name**: Milano Cortina 2026
   - **Slug**: `milano-2026` (lowercase, hyphens only)
   - **Description**: XXV Winter Olympic Games
   - **Start Date**: 2026-02-06
   - **End Date**: 2026-02-22
   - **Active**: ✓ (checked)
4. Click "Create Event"

**Result:** Event created and visible in contest selector

### Creating a New Contest/Pool

1. Visit `/admin/global` or `/admin/global/contests`
2. Click "➕ Create Contest"
3. Fill out the form:
   - **Event**: Select from dropdown (e.g., "Milano Cortina 2026")
   - **Slug**: `office-pool` (lowercase, hyphens only)
   - **Name**: Office Pool 2026
   - **Description**: DTEC office competition
   - **State**: Open (or Setup if still configuring)
   - **Budget**: 200 (total points users can spend)
   - **Max Countries**: 10 (max countries per user)
   - **Deadline**: 2026-02-04T17:00 (UTC)
4. Click "Create Contest"

**Result:** Contest created and accessible at `/<event-slug>/<contest-slug>`

**Example URL:** `/milano-2026/office-pool`

### Editing Events/Contests

**Events:**
1. Visit `/admin/global/events`
2. Click "Edit" next to any event
3. Modify fields
4. Click "Update Event"

**Contests:**
1. Visit `/admin/global/contests`
2. Click "Edit" next to any contest
3. Modify fields (can change event, settings, etc.)
4. Click "Update Contest"

### Managing a Contest

**From Global Admin:**
1. Visit `/admin/global/contests`
2. Click "Manage" next to the contest

**Result:** Opens contest-specific admin panel at `/<event-slug>/<contest-slug>/admin`

**Contest Admin Can:**
- Edit contest settings (name, state, budget, deadline)
- Import countries for the event
- Enter medals during the Games
- View registered users
- Manage user picks

---

## Architecture

### Role Separation

```
┌─────────────────────────────────────┐
│         GLOBAL ADMIN                │
│  (GLOBAL_ADMIN_EMAILS)              │
│                                     │
│  • Create/edit/delete events       │
│  • Create/edit/delete contests     │
│  • System-wide access              │
│  • Can access ALL contest admin    │
└─────────────────────────────────────┘
                  │
                  ├─────────────────────────────┐
                  │                             │
        ┌─────────▼──────────┐      ┌──────────▼─────────┐
        │   CONTEST ADMIN     │      │   CONTEST ADMIN    │
        │   (ADMIN_EMAILS)    │      │   (ADMIN_EMAILS)   │
        │                     │      │                    │
        │  • Manage Contest 1 │      │  • Manage Contest 2│
        │  • Import countries │      │  • Import countries│
        │  • Enter medals     │      │  • Enter medals    │
        │  • Manage users     │      │  • Manage users    │
        └─────────────────────┘      └────────────────────┘
```

**Current State:**
- Both `ADMIN_EMAILS` and `GLOBAL_ADMIN_EMAILS` default to `ken@corless.com`
- Ken has both global and contest-level admin access

**Future State:**
- `GLOBAL_ADMIN_EMAILS` - Small group of system administrators
- `ADMIN_EMAILS` - Contest-specific admins per contest
- Could add per-contest admin assignment in database

### URL Structure

```
/admin/global                           # Global admin dashboard
/admin/global/events                    # Manage all events
/admin/global/events/create             # Create new event
/admin/global/events/<id>/edit          # Edit specific event
/admin/global/contests                  # Manage all contests
/admin/global/contests/create           # Create new contest
/admin/global/contests/<id>/edit        # Edit specific contest

/<event-slug>/<contest-slug>/admin      # Contest-specific admin
/<event-slug>/<contest-slug>/admin/contest    # Contest settings
/<event-slug>/<contest-slug>/admin/countries  # Country management
/<event-slug>/<contest-slug>/admin/medals     # Medal entry
/<event-slug>/<contest-slug>/admin/users      # User management
```

---

## Database Schema

**Events and Contests:**
```sql
-- Events (Olympic Games)
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Contests (pools within events)
CREATE TABLE contest (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    slug TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    state TEXT NOT NULL DEFAULT 'setup',
    budget INTEGER NOT NULL DEFAULT 200,
    max_countries INTEGER NOT NULL DEFAULT 10,
    deadline TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, slug)
);
```

**Relationship:**
- One event can have many contests
- Each contest belongs to one event
- Slug must be unique within an event (allows `office-pool` for multiple events)
- Countries are scoped to events
- Picks are scoped to contests

---

## Security

**Authorization Checks:**
1. `@global_admin_required` - Checks `GLOBAL_ADMIN_EMAILS`
2. `@admin_required` - Checks `ADMIN_EMAILS`
3. Both decorators require login (`@login_required` implicit)
4. Returns 401 if not logged in
5. Returns 403 if logged in but not authorized

**Case-Insensitive:**
- All email checks are case-insensitive
- `ken@corless.com` = `Ken@Corless.com` = `KEN@CORLESS.COM`

**URL Security:**
- Event/contest slugs validated (lowercase, hyphens, numbers only)
- Prevents directory traversal
- Prevents SQL injection (parameterized queries)

---

## Testing

**Manual Testing Steps:**

1. **Test Global Admin Access:**
   ```bash
   # Start server
   flask run --debug --port 5002

   # Visit http://localhost:5002/
   # Login as ken@corless.com
   # Click "🌐 Global Admin" in navigation
   # Should see dashboard
   ```

2. **Test Event Creation:**
   ```
   # From Global Admin dashboard
   # Click "➕ Create Event"
   # Fill form with Paris 2024 data
   # Submit
   # Verify event appears in events list
   ```

3. **Test Contest Creation:**
   ```
   # From Global Admin dashboard
   # Click "➕ Create Contest"
   # Select event, fill form
   # Submit
   # Verify contest appears in contests list
   # Visit /<event-slug>/<contest-slug>
   # Verify contest is accessible
   ```

4. **Test Authorization:**
   ```
   # Logout
   # Try to visit /admin/global
   # Should get 401 Unauthorized
   # Login as non-admin user
   # Try to visit /admin/global
   # Should get 403 Forbidden
   ```

**Automated Tests:**
- `test_global_admin.py` - Comprehensive test suite
- Tests dashboard, event creation, contest creation, authorization

---

## Files Modified/Created

| File | Status | Description |
|------|--------|-------------|
| `app/config.py` | Modified | Added GLOBAL_ADMIN_EMAILS configuration |
| `app/decorators.py` | Modified | Added @global_admin_required decorator |
| `app/routes/global_admin.py` | Created | All global admin routes |
| `app/__init__.py` | Modified | Registered global_admin routes |
| `app/templates/base.html` | Modified | Added Global Admin navigation link |
| `app/templates/admin/global/dashboard.html` | Created | System overview |
| `app/templates/admin/global/events.html` | Created | Events list |
| `app/templates/admin/global/event_form.html` | Created | Event create/edit form |
| `app/templates/admin/global/contests.html` | Created | Contests list |
| `app/templates/admin/global/contest_form.html` | Created | Contest create/edit form |
| `test_global_admin.py` | Created | Automated test suite |

---

## Future Enhancements

**Role-Based Access Control:**
- [ ] Per-contest admin assignment (database table)
- [ ] Contest admins can only access their assigned contests
- [ ] Global admins can assign contest admins

**Event Management:**
- [ ] Delete events (with cascade to contests)
- [ ] Clone events (copy structure to new year)
- [ ] Event templates (pre-configured settings)

**Contest Management:**
- [ ] Clone contests (duplicate settings/countries)
- [ ] Delete contests (with user data cleanup)
- [ ] Contest templates (office pool, family pool, etc.)
- [ ] Bulk contest creation (create multiple at once)

**Audit Log:**
- [ ] Track all admin actions
- [ ] View history of changes
- [ ] Rollback capability

**Permissions:**
- [ ] Fine-grained permissions (can create but not delete)
- [ ] Team-based admin groups
- [ ] Delegated administration

---

## Summary

✅ **Global Admin System Complete**
✅ **Separate from Contest Admin**
✅ **Create/Manage Events and Contests**
✅ **Navigation Integration**
✅ **Role-Based Access Ready**

**Access:** Login as `ken@corless.com` → Click "🌐 Global Admin"

**Next Steps:**
1. Create additional events for future Olympics
2. Create multiple contests per event
3. Configure contest settings (budget, countries, deadlines)
4. Invite users to register for specific contests

---

**Global Admin:** System-wide control for platform administrators
**Contest Admin:** Contest-specific management for pool organizers

The architecture is ready for future role separation and advanced permissions! 🎉
