# Railway Deployment Guide - pool2.mccountdown.com

Deploy the Wikipedia auto-scraping feature to a new Railway instance for safe testing.

## Prerequisites

✅ Local testing complete
✅ All changes committed to `singleauto` branch
✅ Railway CLI installed
✅ Logged into Railway

---

## Step 1: Push Branch to GitHub

```bash
cd /Users/kcorless/Documents/Projects/OlympicPool

# Push singleauto branch to GitHub
git push origin singleauto
```

---

## Step 2: Create New Railway Project

### Via Railway Dashboard (Recommended)

1. Go to: https://railway.app/
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose: **maccorless/OlympicPool**
5. Configure:
   - **Branch:** `singleauto`
   - **Name:** "Olympic Pool 2 - Auto-Scraping Test"
   - **Root Directory:** Leave blank
   - **Build Command:** (auto-detected)
   - **Start Command:** `gunicorn -w 4 -b 0.0.0.0:$PORT 'app:create_app()'`

### Via Railway CLI (Alternative)

```bash
cd /Users/kcorless/Documents/Projects/OlympicPool
railway login
railway init
# Select: Create new project
# Name: Olympic Pool 2 - Auto-Scraping Test

railway link
# Select the project you just created

railway up
```

---

## Step 3: Configure Environment Variables

In Railway dashboard → Your Project → Variables, add:

### Required Variables

```bash
# Flask
FLASK_SECRET_KEY=<generate-new-32-char-random-string>
BASE_URL=https://pool2.mccountdown.com

# Admin Access
ADMIN_EMAILS=ken@corless.com

# Twilio SMS (copy from your existing .env file)
TWILIO_ACCOUNT_SID=<your-twilio-account-sid>
TWILIO_AUTH_TOKEN=<your-twilio-auth-token>
TWILIO_VERIFY_SERVICE_SID=<your-twilio-verify-service-sid>

# SMS Mode (False for production)
NO_SMS_MODE=False

# Medal Auto-Update
MEDAL_STALENESS_SECONDS=900

# Database Path (Railway)
DATABASE_DIR=/app/instance

# Session Security (True for production)
SESSION_COOKIE_SECURE=True
```

### Generate FLASK_SECRET_KEY

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Step 4: Configure Custom Domain

### In Railway Dashboard

1. Go to: Your Project → Settings → Domains
2. Click **"Add Domain"**
3. Enter: `pool2.mccountdown.com`
4. Railway will provide a CNAME target (e.g., `xxx.railway.app`)

### Update DNS (Your Domain Provider)

Add CNAME record:
- **Type:** CNAME
- **Name:** pool2
- **Target:** `<railway-provided-target>`
- **TTL:** 300 (or auto)

**DNS Propagation:** Takes 5-60 minutes

---

## Step 5: Verify Deployment

### Check Railway Logs

```bash
railway logs
```

Look for:
- ✅ Flask app starting
- ✅ No import errors
- ✅ Gunicorn workers spawned

### Test Basic Endpoints

```bash
# Health check (once DNS propagates)
curl https://pool2.mccountdown.com/

# Or use Railway's generated domain first
curl https://olympic-pool-2-production.up.railway.app/
```

---

## Step 6: Initialize Database

### Option A: Fresh Database (Recommended for Testing)

Railway will auto-create SQLite database on first run. The schema will be initialized from `schema.sql`.

To verify:
```bash
railway shell
sqlite3 instance/medal_pool.db "SELECT COUNT(*) FROM contest;"
```

### Option B: Import Existing Data

**If you want to copy data from production:**

```bash
# On local machine - download from old production
railway link  # Link to OLD production project
railway run sqlite3 instance/medal_pool.db .dump > production_data.sql

# Link to NEW project
railway unlink
railway link  # Select pool2 project

# Upload and import
railway run "sqlite3 instance/medal_pool.db < production_data.sql"
```

---

## Step 7: Run Migration

**IMPORTANT:** Add the `wikipedia_medal_url` column:

```bash
railway run python migrations/add_wikipedia_url_to_contest.py
```

Should output:
```
✅ Migration completed successfully!
```

Verify:
```bash
railway run sqlite3 instance/medal_pool.db "SELECT wikipedia_medal_url FROM contest WHERE id = 1;"
```

Should show:
```
https://en.wikipedia.org/wiki/2026_Winter_Olympics_medal_table
```

---

## Step 8: Create Admin User

### If starting with fresh database:

```bash
railway shell

# Inside shell
sqlite3 instance/medal_pool.db

# SQL commands:
INSERT INTO users (email, phone_number, name, team_name)
VALUES ('ken@corless.com', '+13126183399', 'Ken Corless', 'Admin Team');
```

---

## Step 9: Test Wikipedia Scraping

1. **Login as admin:**
   - Go to: https://pool2.mccountdown.com/login
   - Phone: +13126183399
   - Enter OTP from SMS

2. **Test manual scrape:**
   - Go to: https://pool2.mccountdown.com/admin/medals
   - Click "📚 Refresh from Wikipedia"
   - Should update medals and show success message

3. **Set contest to locked state:**
   ```bash
   railway run sqlite3 instance/medal_pool.db "UPDATE contest SET state = 'locked' WHERE id = 1;"
   ```

4. **Test auto-refresh:**
   - Visit: https://pool2.mccountdown.com/leaderboard
   - Wait 15 minutes
   - Visit again - should auto-scrape in background
   - Check logs: `railway logs`

---

## Step 10: Monitor and Verify

### Check Medal Data

```bash
railway run sqlite3 instance/medal_pool.db "SELECT SUM(gold) + SUM(silver) + SUM(bronze) FROM medals;"
```

Should show current Wikipedia medal count (e.g., 33).

### Check Scrape Metadata

```bash
railway run sqlite3 instance/medal_pool.db "SELECT value FROM system_meta WHERE key = 'medals_last_scrape';"
```

Should show JSON with scrape results.

### Monitor Logs

```bash
railway logs --follow
```

Look for:
- `"Triggered background Wikipedia scrape"`
- `"Successfully scraped medals for X countries"`
- No errors

---

## Troubleshooting

### Deployment Failed

Check Railway logs:
```bash
railway logs
```

Common issues:
- Missing environment variables
- Python version mismatch (need 3.11+)
- Missing dependencies in requirements.txt

### Database Not Created

```bash
railway shell
ls -la instance/
```

If missing, create directory:
```bash
mkdir -p instance
sqlite3 instance/medal_pool.db < schema.sql
```

### Domain Not Working

1. Check DNS propagation: https://dnschecker.org/#CNAME/pool2.mccountdown.com
2. Verify CNAME points to Railway domain
3. Wait up to 60 minutes for propagation

### Migration Failed

```bash
railway run python migrations/add_wikipedia_url_to_contest.py
```

If column already exists, it will skip safely.

### Wikipedia Scraping Not Triggering

Check:
1. Contest state is "locked" or "complete"
2. MEDAL_STALENESS_SECONDS is set (default 900)
3. Medal data is older than staleness threshold
4. Wikipedia URL is configured in contest table

---

## Rollback Plan

If issues occur, you can:

1. **Keep old production running** - it's unaffected
2. **Delete Railway project** - start fresh
3. **Revert DNS** - point back to old production

The old production instance continues to run independently.

---

## Success Checklist

✅ Railway project created and deployed
✅ Custom domain configured (pool2.mccountdown.com)
✅ Environment variables set
✅ Database initialized
✅ Migration run successfully
✅ Admin user can login
✅ Manual Wikipedia scrape works
✅ Auto-refresh triggers after 15 minutes
✅ Leaderboard displays correctly
✅ No errors in Railway logs

---

## Next Steps After Successful Test

Once pool2.mccountdown.com is verified stable:

**Option A:** Point main domain to new instance
- Update DNS: `pool.mccountdown.com` → new Railway instance
- Keep old instance as backup

**Option B:** Keep both instances
- Old: `pool.mccountdown.com` (current contest)
- New: `pool2.mccountdown.com` (future contests with auto-scraping)
