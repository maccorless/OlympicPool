# Quick Troubleshooting Guide

**If you see this error, here's the fix:**

---

## Error: "TypeError: Object of type Row is not JSON serializable"

**Location:** Template rendering with `{{ data|tojson }}`

**Fix:**
```python
# Before passing to template:
rows = db.execute('SELECT * FROM table').fetchall()
data = [dict(row) for row in rows]  # Convert to dicts
return render_template('page.html', data=data)
```

**See:** CLAUDE.md section "1. SQLite Row Objects Are Not JSON Serializable"

---

## Error: "Alpine Expression Error: Unexpected token '}'"

**Location:** Browser console when page loads

**Root Cause:** Alpine.js trying to initialize before JavaScript function is defined

**Fix:** Move `<script>` tag BEFORE the `<div x-data>`:
```html
<!-- CORRECT order: -->
{% block content %}
<script>
function myComponent() {
  return { ... }
}
</script>

<div x-data="myComponent()">
  ...
</div>
{% endblock %}
```

**See:** CLAUDE.md section "2. Alpine.js Script Placement and Initialization"

---

## Error: "Uncaught ReferenceError: isSelected is not defined"

**Location:** Browser console, in Alpine.js component

**Root Cause:** Using Jinja `{% for %}` loop instead of Alpine.js `<template x-for>`

**Fix:**
```html
<!-- ❌ WRONG -->
{% for item in items %}
  <div :class="{ 'selected': isSelected(item.id) }">
{% endfor %}

<!-- ✅ CORRECT -->
<template x-for="item in items" :key="item.id">
  <div :class="{ 'selected': isSelected(item.id) }">
</template>
```

**See:** CLAUDE.md section "3. Alpine.js Scope: Server-Side Loops vs Client-Side Loops"

---

## Error: Browser shows "Leave site? Changes you made may not be saved"

**Location:** When clicking "Save Picks" button

**Root Cause:** `beforeunload` event handler doesn't know form is being intentionally submitted

**Fix:** Add `isSubmitting` flag:
```javascript
return {
  isSubmitting: false,

  submitPicks() {
    if (this.canSubmit()) {
      this.isSubmitting = true;  // NEW
      document.getElementById('draft-form').submit();
    }
  },

  warnIfUnsaved(event) {
    if (this.isSubmitting) return;  // NEW
    if (this.selected.length > 0) {
      event.preventDefault();
      event.returnValue = '';
    }
  }
}
```

**See:** CLAUDE.md section "4. Browser Navigation Warnings (beforeunload)"

---

## Issue: User's existing picks not showing when editing

**Location:** Draft picker shows empty on "Edit Picks"

**Root Cause:** Not fetching or passing existing selections to Alpine.js

**Fix:**
```python
# Backend - fetch existing picks
existing_picks = db.execute('''
    SELECT country_code FROM picks WHERE user_id = ?
''', [user['id']]).fetchall()

selected_codes = [p['country_code'] for p in existing_picks]

return render_template('draft/picker.html',
                     selected_codes=selected_codes,  # Pass to template
                     ...)
```

```html
<!-- Frontend - initialize with existing selections -->
<div x-data="draftPicker({{ selected_codes|tojson|safe }}, ...)">
```

**See:** CLAUDE.md section "5. Preserving User Selections When Editing"

---

## Issue: Flask not reloading when code changes

**Location:** Development - have to manually restart server

**Fix:** Add to `.env`:
```bash
FLASK_DEBUG=True
```

Or run with:
```bash
flask run --debug
```

**IMPORTANT:** Never use `FLASK_DEBUG=True` in production!

**See:** CLAUDE.md section "6. Flask Auto-Reload During Development"

---

## Error: JavaScript sees HTML entities instead of JSON

**Location:** Console shows `{&quot;key&quot;: &quot;value&quot;}` instead of valid JSON

**Root Cause:** Missing `|safe` filter after `|tojson`

**Fix:**
```html
<!-- ❌ WRONG -->
<script>
const data = {{ my_data|tojson }};
</script>

<!-- ✅ CORRECT -->
<script>
const data = {{ my_data|tojson|safe }};
</script>
```

**See:** CLAUDE.md section "9. Jinja Template Filters for Safety"

---

## Error: "invalid or expired link" on magic link click

**Location:** User clicks magic link from email

**Possible causes:**

1. **Token already used:**
   - Check `used_at IS NULL` in query
   - Mark token as used after verification: `UPDATE tokens SET used_at = CURRENT_TIMESTAMP`

2. **Token expired:**
   - Check `expires_at > CURRENT_TIMESTAMP` in query
   - Tokens expire after 15 minutes by default

3. **Token not in database:**
   - Check token generation code
   - Verify email sending succeeded

**See:** CLAUDE.md section "10. Magic Link Implementation Details"

---

## Error: 403 Forbidden on admin routes

**Location:** Trying to access `/admin/*` routes

**Root Cause:** User email not in `ADMIN_EMAILS` config

**Fix:** Add to `.env`:
```bash
ADMIN_EMAILS=your@email.com,another@email.com
```

**Important:** Use the exact email address you registered with (case-sensitive)

**See:** CLAUDE.md section "11. Admin Email Configuration"

---

## Issue: User's picks partially saved after error

**Location:** Some picks saved, some not

**Root Cause:** Not using database transactions

**Fix:** Wrap in transaction:
```python
try:
    db.execute('BEGIN')

    db.execute('DELETE FROM picks WHERE user_id = ?', [user['id']])

    for code in country_codes:
        db.execute('INSERT INTO picks (user_id, country_code) VALUES (?, ?)',
                   [user['id'], code])

    db.commit()  # All or nothing
except sqlite3.Error as e:
    db.rollback()  # Undo everything on error
    raise
```

**See:** CLAUDE.md section "7. Atomic Database Operations for Picks"

---

## Quick Diagnostic Steps

1. **Check Flask terminal** for Python errors (syntax, imports, database)
2. **Check browser console** for JavaScript errors (Alpine.js, JSON parsing)
3. **View page source** to see actual rendered HTML vs template
4. **Add console.log** in Alpine.js component initialization to verify data
5. **Check network tab** for failed requests (404, 422, 500)

---

## Still Stuck?

1. Read the full explanation in **CLAUDE.md "Common Pitfalls & Solutions"** section
2. Review working examples in:
   - `app/templates/draft/picker.html` - Alpine.js component
   - `app/routes/draft.py` - Backend implementation
   - `app/routes/auth.py` - Magic link implementation
3. Check **IMPLEMENTATION_LESSONS.md** for top 3 critical issues

---

## Prevention Checklist

Before implementing a feature, verify:

- [ ] Using `[dict(row) for row in rows]` before passing to templates with `|tojson`
- [ ] JavaScript functions defined BEFORE HTML that uses them
- [ ] Using `<template x-for>` when accessing Alpine.js component scope
- [ ] Using `{{ data|tojson|safe }}` when passing to JavaScript
- [ ] Atomic transactions for multi-step database operations
- [ ] `FLASK_DEBUG=True` in `.env` for development

See full checklist in CLAUDE.md "Implementation Checklist" section.
