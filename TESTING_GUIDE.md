# Multi-Contest Implementation - Testing Guide

## ✅ Automated Tests

Run the automated test suite:
```bash
python3 test_multi_contest.py
```

This tests:
- Database schema correctness
- Default data presence
- Contest isolation
- Data consistency
- Query performance

---

## 🧪 Manual Testing Workflow

### Prerequisites
```bash
# Ensure you're on multi branch
git checkout multi
git status

# Activate virtual environment
source .venv/bin/activate

# Verify database is initialized
ls -la instance/medal_pool.db

# Start Flask app
flask run
```

---

### Test 1: Contest Selector & Home Page

**Steps:**
1. Visit `http://localhost:5001/`
2. Should see "Olympic Medal Pool Contests" page
3. Should show "Milano Cortina 2026 - XXV Winter Olympic Games"
4. Click on the contest

**Expected Result:**
- Redirects to `/milano-2026/default`
- Shows contest home or login page (if not logged in)

**✓ Pass Criteria:**
- Contest selector displays
- Contest card is clickable
- URL includes event and contest slugs

---

### Test 2: User Registration Flow

**Steps:**
1. From `/milano-2026/default`, click "Register"
2. Fill out form:
   - Name: "Test User"
   - Email: "test@example.com" (use real email if testing email)
   - Team Name: "Dream Team"
3. Submit form

**Expected Result:**
- Redirects to "Check Your Email" page
- Magic link displayed (in dev mode with `NO_EMAIL_MODE`)
- Database check:
  ```sql
  SELECT * FROM users WHERE email = 'test@example.com';
  SELECT * FROM user_contest_info WHERE user_id = (SELECT id FROM users WHERE email = 'test@example.com');
  ```
  Both should have records

**✓ Pass Criteria:**
- User created in `users` table
- `user_contest_info` entry created with `contest_id=1` and team name
- Magic link works

---

### Test 3: Magic Link & Login

**Steps:**
1. Click magic link from "Check Your Email" page
2. Should log in automatically

**Expected Result:**
- Redirects to `/milano-2026/default/draft`
- Navigation shows "Leaderboard", "My Picks", "Logout"
- Session is active

**✓ Pass Criteria:**
- Login successful
- Correct redirect to contest home
- Navigation updated for logged-in user

---

### Test 4: Draft Picker

**Steps:**
1. On `/milano-2026/default/draft` page
2. Select 5-10 countries (within budget of 200)
3. Click "Save Picks"

**Expected Result:**
- Success message: "Your picks have been saved!"
- Redirects to `/milano-2026/default/my-picks`
- Database check:
  ```sql
  SELECT * FROM picks WHERE user_id = 1;
  ```
  Should show picks with `contest_id=1` and `event_id=1`

**✓ Pass Criteria:**
- Countries selectable
- Budget tracking works
- Picks saved with correct `contest_id` and `event_id`
- Validation works (budget, max countries)

---

### Test 5: My Picks Page

**Steps:**
1. Visit `/milano-2026/default/my-picks`
2. Verify your picks are displayed
3. Click "Edit Picks"

**Expected Result:**
- All selected countries displayed
- Cost and totals calculated
- Edit button returns to draft picker with selections preserved

**✓ Pass Criteria:**
- Picks displayed correctly
- Totals match selections
- Edit preserves current selections

---

### Test 6: Leaderboard (Open State)

**Steps:**
1. Visit `/milano-2026/default/leaderboard`
2. Contest state should be "open"

**Expected Result:**
- Shows team names only
- All users at rank #1
- No medals/flags displayed
- Sortable columns (name)

**✓ Pass Criteria:**
- Leaderboard visible in "open" state
- No medal data shown (contest not locked yet)
- Current user's row highlighted

---

### Test 7: Admin Dashboard

**Steps:**
1. Add your email to `.env`:
   ```
   ADMIN_EMAILS=your@email.com
   ```
2. Restart Flask
3. Visit `/milano-2026/default/admin`

**Expected Result:**
- Admin dashboard displays
- Shows stats for this contest:
  - Total users (count from user_contest_info)
  - Users with picks
  - Total countries
  - Medals entered

**✓ Pass Criteria:**
- Admin dashboard accessible
- Stats show contest-specific data
- Navigation includes admin links

---

### Test 8: Contest State Management

**Steps:**
1. In admin, click "Contest Settings"
2. Change state from "setup" to "open"
3. Save

**Expected Result:**
- Contest state updated
- Database check:
  ```sql
  SELECT state FROM contest WHERE id = 1;
  ```
  Should show "open"

**✓ Pass Criteria:**
- State change saves
- Only affects contest id=1
- Redirects back to admin

---

### Test 9: Medal Entry

**Steps:**
1. Change contest state to "locked"
2. Visit `/milano-2026/default/admin/medals`
3. Enter medals for a few countries:
   - Norway: 10 gold, 8 silver, 5 bronze
   - Germany: 5 gold, 7 silver, 6 bronze
4. Click "Save Medal Counts"

**Expected Result:**
- Medals saved successfully
- Database check:
  ```sql
  SELECT * FROM medals WHERE event_id = 1;
  ```
  Shows medals with correct `event_id`
- Points calculated: gold×3 + silver×2 + bronze×1

**✓ Pass Criteria:**
- Medals save with `event_id=1`
- Points calculated correctly
- Filtered by event (no cross-event medals)

---

### Test 10: Leaderboard (Locked State)

**Steps:**
1. Visit `/milano-2026/default/leaderboard`
2. Contest state is "locked"

**Expected Result:**
- Full leaderboard displayed
- Ranks calculated by points
- Flags shown for each country
- Medal counts visible
- Current user's row highlighted

**✓ Pass Criteria:**
- Leaderboard shows medal data
- Ranks correct (with tiebreakers)
- Country flags display
- Sortable by columns

---

### Test 11: Multi-Contest Isolation (Advanced)

**Setup:**
Create a second contest manually:
```sql
sqlite3 instance/medal_pool.db

INSERT INTO contest (id, event_id, slug, name, description, state, budget, max_countries, deadline)
VALUES (2, 1, 'office-pool', 'Office Pool 2026', 'DTEC office competition', 'open', 300, 15, '2026-02-04T17:00:00Z');
```

**Steps:**
1. Register a NEW user for the second contest at `/milano-2026/office-pool/register`
2. Draft different countries
3. Check database isolation:
   ```sql
   -- Contest 1 picks
   SELECT COUNT(*) FROM picks WHERE contest_id = 1;

   -- Contest 2 picks
   SELECT COUNT(*) FROM picks WHERE contest_id = 2;

   -- User registrations
   SELECT u.email, c.name, uci.team_name
   FROM user_contest_info uci
   JOIN users u ON uci.user_id = u.id
   JOIN contest c ON uci.contest_id = c.id;
   ```

**Expected Result:**
- Contest 1 and 2 have separate picks
- Same user can join both contests
- Leaderboards show different users
- Admin dashboards show contest-specific stats

**✓ Pass Criteria:**
- Picks isolated by `contest_id`
- User can join multiple contests with different team names
- No data leakage between contests

---

## 🐛 Common Issues & Solutions

### Issue 1: "404 Not Found" on contest pages
**Cause:** Routes not registered or event/contest slugs wrong
**Fix:**
- Check routes are registered in `app/__init__.py`
- Verify URL structure: `/<event_slug>/<contest_slug>/...`

### Issue 2: "contest_id" column doesn't exist
**Cause:** Old database without multi-contest schema
**Fix:**
```bash
rm instance/medal_pool.db
flask init-db
sqlite3 instance/medal_pool.db < data/countries.sql
```

### Issue 3: No countries showing in draft
**Cause:** Countries not loaded or wrong event_id
**Fix:**
```bash
sqlite3 instance/medal_pool.db < data/countries.sql
```

### Issue 4: Admin links don't work
**Cause:** Email not in `ADMIN_EMAILS`
**Fix:**
```bash
# Add to .env
ADMIN_EMAILS=your@email.com
# Restart Flask
```

### Issue 5: Picks not saving
**Cause:** Validation error or contest state not "open"
**Fix:**
- Check Flask logs for validation errors
- Verify contest state: `SELECT state FROM contest WHERE id = 1;`
- Should be "open" to allow picks

---

## 📊 Success Metrics

**All tests pass when:**

✓ Database schema has multi-contest structure
✓ Default event and contest created
✓ Users can register and login with contest context
✓ Picks save with `contest_id` and `event_id`
✓ Leaderboard filters by contest
✓ Admin functions work per-contest
✓ No hardcoded `WHERE id = 1` in route queries
✓ All templates use dynamic URLs with `url_for()`
✓ Navigation works throughout the app
✓ Medal data scoped to events
✓ Countries scoped to events
✓ Multi-contest isolation verified (optional)

---

## 🚀 Next Steps

After local testing passes:

1. **Commit changes:**
   ```bash
   git add .
   git commit -m "Complete multi-contest migration"
   ```

2. **Deploy to staging:**
   - Create new Railway instance for multi branch
   - Test with production-like environment
   - Verify email delivery (if not using NO_EMAIL_MODE)

3. **Production deployment:**
   - Merge to main branch (when ready)
   - Run migration script on production DB
   - Monitor for errors

---

**Testing completed on:** 2026-01-25
**Implementation status:** ✅ Complete
**All phases:** Foundation, Auth, Draft, Leaderboard, Admin, Templates ✓
