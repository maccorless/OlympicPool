# Implementation Lessons Learned

**Date:** January 14, 2025
**Purpose:** Quick reference of critical mistakes to avoid when building from scratch

---

## What We Updated

### 1. CLAUDE.md - Added "Common Pitfalls & Solutions" Section

A comprehensive new section (495 lines) documenting 12 common implementation issues and their solutions:

1. **SQLite Row JSON Serialization** - Row objects can't be converted to JSON
2. **Alpine.js Script Placement** - Functions must be defined before HTML uses them
3. **Alpine.js Scope Issues** - When to use Jinja vs Alpine.js loops
4. **Browser Navigation Warnings** - Preventing false "leave site?" warnings
5. **Preserving User Selections** - How to load existing picks when editing
6. **Flask Auto-Reload** - Setting FLASK_DEBUG=True for development
7. **Atomic Database Operations** - Using transactions for data integrity
8. **Server-Side Validation** - Dynamic SQL with placeholders
9. **Jinja Template Filters** - Using `|tojson|safe` correctly
10. **Magic Link Implementation** - Single-use, expiring tokens
11. **Admin Email Configuration** - Setting up admin access
12. **Route Registration Pattern** - Simple approach without blueprints

### 2. CLAUDE.md - Added "Implementation Checklist"

Pre-flight checklist for each major feature:
- Draft Picker (8 items)
- Magic Links (5 items)
- Database Operations (4 items)
- Templates (4 items)

### 3. PRD - Added "Critical Implementation Notes" Section

Added section 12.4 with high-level summary and pointer to CLAUDE.md for details.

Updated companion documents table to emphasize CLAUDE.md is **MUST READ**.

### 4. Document History

Updated both files with version 1.6 noting the comprehensive pitfalls documentation.

---

## Top 3 Most Critical Lessons

### 🔴 #1: Alpine.js Script Placement
```html
<!-- ❌ WRONG - Will break with "Unexpected token" error -->
<div x-data="draftPicker()">...</div>
<script>function draftPicker() {...}</script>

<!-- ✅ CORRECT - Script BEFORE usage -->
<script>function draftPicker() {...}</script>
<div x-data="draftPicker()">...</div>
```

### 🔴 #2: SQLite Row to Dict Conversion
```python
# ❌ WRONG - TypeError: Object of type Row is not JSON serializable
countries = db.execute('SELECT * FROM countries').fetchall()
return render_template('page.html', countries=countries)

# ✅ CORRECT - Convert to dicts first
countries_rows = db.execute('SELECT * FROM countries').fetchall()
countries = [dict(row) for row in countries_rows]
return render_template('page.html', countries=countries)
```

### 🔴 #3: Alpine.js Scope - Use Client-Side Loops
```html
<!-- ❌ WRONG - isSelected() not in scope -->
{% for country in countries %}
  <div :class="{ 'selected': isSelected('{{ country.code }}') }">
{% endfor %}

<!-- ✅ CORRECT - Alpine.js loop keeps scope -->
<template x-for="country in countries" :key="country.code">
  <div :class="{ 'selected': isSelected(country.code) }">
</template>
```

---

## Before You Start Coding

1. **Read CLAUDE.md "Common Pitfalls & Solutions"** (lines 831-1321)
2. **Review "Implementation Checklist"** (lines 1288-1320)
3. **Keep this summary handy** for quick reference

---

## Why This Matters

Without these documented learnings, you will encounter:
- 3-4 hours of debugging Alpine.js initialization errors
- Multiple iterations on the draft picker getting scope right
- Confusion about why existing selections aren't loading
- False navigation warnings frustrating users
- Potential data integrity issues with non-atomic saves

**These notes save you from repeating all these mistakes.**

---

## Related Files

- `/Users/kcorless/Documents/Projects/OlympicPool/CLAUDE.md` - Complete technical guide
- `/Users/kcorless/Documents/Projects/OlympicPool/olympic-medal-pool-prd.md` - Product requirements
- `/Users/kcorless/Documents/Projects/OlympicPool/app/templates/draft/picker.html` - Working example of all fixes
- `/Users/kcorless/Documents/Projects/OlympicPool/app/routes/draft.py` - Backend implementation example
