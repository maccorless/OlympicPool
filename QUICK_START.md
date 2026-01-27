# Multi-Contest Implementation - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Verify Setup
```bash
# You're already on multi branch
git status  # Should show "On branch multi"

# Database already initialized
ls -la instance/medal_pool.db  # Should exist

# Countries already loaded (58 countries)
sqlite3 instance/medal_pool.db "SELECT COUNT(*) FROM countries WHERE event_id = 1;"
```

### 2. Start the App
```bash
# Activate virtual environment
source .venv/bin/activate

# Start Flask
flask run
```

### 3. Test It Out
**Open browser:** `http://localhost:5001/`

**You should see:**
- Contest selector page
- "Milano Cortina 2026 - XXV Winter Olympic Games" card
- Clean, working interface

**Click the contest → Should redirect to:** `/milano-2026/default`

---

## ✅ Quick Verification

### Run Automated Tests
```bash
python3 test_multi_contest.py
```

**Expected output:**
```
All 5 tests PASSED! ✓
```

### Manual Smoke Test (2 minutes)
1. Visit `http://localhost:5001/`
2. Click contest → lands on `/milano-2026/default`
3. Click "Register" → form works
4. Fill out form and submit
5. Magic link displayed (dev mode)
6. Click magic link → lands on `/milano-2026/default/draft`

**If all 6 steps work → ✅ Implementation is working!**

---

## 📖 Full Documentation

- **Testing Guide:** `TESTING_GUIDE.md` (11 detailed test scenarios)
- **Implementation Summary:** `IMPLEMENTATION_COMPLETE.md` (full change log)
- **Project Instructions:** `CLAUDE.md` (authoritative implementation guide)

---

## 🐛 Quick Troubleshooting

### App won't start
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check .env exists
ls -la .env
```

### No countries in draft
```bash
sqlite3 instance/medal_pool.db < data/countries.sql
```

### Can't access admin
```bash
# Add your email to .env
echo "ADMIN_EMAILS=your@email.com" >> .env
flask run  # Restart
```

---

## 🎯 What Changed?

**Before:** Single hardcoded contest
**After:** Support for multiple contests per event

**Key URLs:**
- Home: `/` → Contest selector
- Contest: `/milano-2026/default` → Contest home
- Register: `/milano-2026/default/register`
- Draft: `/milano-2026/default/draft`
- Leaderboard: `/milano-2026/default/leaderboard`
- Admin: `/milano-2026/default/admin`

**Database:**
- New: `events` table
- New: `user_contest_info` table (replaces `users.team_name`)
- Modified: All tables now support multi-contest

---

## ✨ Key Features

✅ Users can join multiple contests
✅ Each contest has isolated data
✅ Admin can manage per-contest
✅ Clean URLs with event/contest slugs
✅ Same user can have different team names per contest

---

**Ready to test?** Run `flask run` and visit `http://localhost:5001/` 🎉
