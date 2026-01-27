# Shared Infrastructure Guide

This guide explains what infrastructure can be shared between your existing single-contest app and the new multi-contest OlympicPool2 deployment.

## ✅ Can Be Shared (No Need to Recreate)

### 1. Twilio Account & Credentials ✅ REUSE

**You can use the EXACT SAME Twilio credentials for both apps.**

```bash
# Use the same values in both Railway projects:
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_VERIFY_SERVICE_SID=VAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Why this works:**
- Twilio doesn't care which app sends verification requests
- The verification codes are just phone number + code validations
- Both apps can share the same Verify service
- You'll only be charged once per SMS, not per app

**Benefits:**
- No additional Twilio setup needed
- No extra cost
- Same SMS delivery behavior
- Unified Twilio dashboard for monitoring

---

### 2. Resend Account & API Key ✅ REUSE (if using email)

**You can use the same Resend API key for both apps.**

```bash
# Use the same value in both Railway projects:
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxx
```

**Why this works:**
- Resend API keys are account-level, not project-specific
- Both apps can send emails from the same sender address
- Free tier covers both apps (if not high volume)

**Optional: Different Sender Addresses**
If you want to distinguish emails from each app:
- Old app: noreply@medalpool.com
- New app: pool@medalpool.com or noreply@app.medalpool.com

But this is optional - same sender works fine.

---

### 3. Admin Email Addresses ✅ REUSE

**You can use the same admin email addresses.**

```bash
# Use the same values in both Railway projects:
ADMIN_EMAILS=your@email.com,other@email.com
GLOBAL_ADMIN_EMAILS=your@email.com
```

**Why this works:**
- Just configuration, not infrastructure
- You're the admin of both apps
- No cost or setup required

---

### 4. Railway Account ✅ REUSE

**Both apps run under your same Railway account.**

- Single Railway dashboard shows both projects
- Single billing for both (but separate usage)
- Can manage both from same CLI session

**Railway CLI:**
```bash
# List all your projects
railway projects

# Switch between projects
railway link  # Select which project to work with
```

---

### 5. Domain Registrar Account ✅ REUSE

**Your domain medalpool.com is already registered.**

You have options for how to use it:

**Option A: Move domain to new app (Recommended per plan)**
- Point medalpool.com to new multi-contest app
- Point old app to subdomain: old.medalpool.com or v1.medalpool.com
- Advantage: Clean primary domain for new app

**Option B: Use subdomain for new app**
- Keep medalpool.com for old app
- Use app.medalpool.com or multi.medalpool.com for new app
- Advantage: No disruption to current users

**Option C: Run both apps on same domain (Advanced)**
- Use Railway's path-based routing (if available)
- Or use a reverse proxy
- Complex, not recommended

---

## ❌ Cannot Be Shared (Must Create New)

### 1. Railway Project ❌ CREATE NEW

**Each app needs its own Railway project.**

**Why:**
- Different codebases
- Different databases (schemas differ)
- Independent deployments
- Separate environment variables
- Separate resource allocation

**How to create:**
```bash
cd /Users/kcorless/Documents/Projects/OlympicPool2
railway init
# Name it: olympic-medal-pool-multi
```

**Cost Impact:**
- Each project counts toward your Railway plan
- Developer Plan ($20/mo) supports multiple projects
- No extra cost if you're already on Developer Plan

---

### 2. Railway Volume (Database Storage) ❌ CREATE NEW

**Each app needs its own volume for database persistence.**

**Why:**
- Databases have different schemas
- Old app: single contest table
- New app: events + contests tables
- Cannot share SQLite file between different schemas

**How to create:**
```bash
railway volume add --mount-path /app/instance
```

**Cost Impact:**
- 1GB volume: Included in plan
- Additional storage: $0.25/GB/month
- New app needs 1GB = Included (no extra cost)

---

### 3. Database ❌ SEPARATE DATABASES

**Each app has its own SQLite database.**

**Why:**
- Different table structures
- Old: Single contest
- New: Multi-event, multi-contest
- Migration would be complex

**Options:**
1. **Run both apps** (Recommended)
   - Old app: Existing database, existing users continue
   - New app: Fresh database, new events/contests
   - No data migration needed

2. **Migrate users to new app** (Advanced)
   - Export users from old database
   - Import into new database
   - Map to new contest structure
   - Requires custom migration script

**Recommendation:** Run both apps independently initially.

---

### 4. SSL Certificate ❌ AUTO-PROVISIONED

**Each Railway deployment gets its own SSL certificate.**

**Why:**
- Railway automatically provisions Let's Encrypt certificates
- Certificate is tied to domain/subdomain
- medalpool.com → one cert
- app.medalpool.com → separate cert

**Good news:**
- Completely automatic
- No manual setup
- No cost
- Auto-renewal

---

### 5. Gunicorn/Docker Container ❌ SEPARATE

**Each app runs in its own container.**

**Why:**
- Different codebases
- Different dependencies (potentially)
- Independent scaling
- Isolated restarts

**No action needed:**
- Railway handles containerization automatically
- Dockerfile defines the container
- Each deployment is isolated

---

## 💰 Cost Analysis: Shared vs New

### Shared Infrastructure (No Extra Cost)
| Service | Current | After New App | Extra Cost |
|---------|---------|---------------|------------|
| Twilio Account | $X/month | Same | $0 |
| Twilio per SMS | $0.05/SMS | Same rate | $0 |
| Resend API | Free tier | Same | $0 |
| Domain | $12/year | Same | $0 |
| Admin emails | $0 | Same | $0 |

### New Infrastructure (Additional Cost)
| Service | Current | After New App | Extra Cost |
|---------|---------|---------------|------------|
| Railway Project | $20/month | $20/month (separate) | $20/month* |
| Railway Volume | 1GB | 1GB (new) | $0** |
| SSL Certificate | Free | Free (auto) | $0 |

\* **If on Hobby Plan:** Each project needs separate plan (+$20/month)
\* **If on Developer Plan:** Multiple projects included (no extra cost)

\*\* Included in plan (1GB free)

### Total Additional Monthly Cost
- **Hobby Plan:** ~$20-25/month (new project)
- **Developer Plan:** ~$0-5/month (just usage, project included)

**Recommendation:** Upgrade to Developer Plan ($20/month) to run both apps under one plan.

---

## 📋 Setup Checklist

### Before Deploying New App

#### Credentials to Copy from Old App ✅
```bash
# In old Railway project
railway link  # Link to old project
railway variables

# Copy these values:
TWILIO_ACCOUNT_SID=<copy-this>
TWILIO_AUTH_TOKEN=<copy-this>
TWILIO_VERIFY_SERVICE_SID=<copy-this>
RESEND_API_KEY=<copy-this>  # if using
ADMIN_EMAILS=<copy-these>
```

#### New Infrastructure to Create ❌
```bash
# In new project directory
cd /Users/kcorless/Documents/Projects/OlympicPool2

# 1. Create Railway project
railway init

# 2. Create volume
railway volume add --mount-path /app/instance

# 3. Set environment variables (use copied credentials)
railway variables set TWILIO_ACCOUNT_SID="<copied-value>"
railway variables set TWILIO_AUTH_TOKEN="<copied-value>"
railway variables set TWILIO_VERIFY_SERVICE_SID="<copied-value>"
railway variables set RESEND_API_KEY="<copied-value>"
railway variables set ADMIN_EMAILS="<copied-emails>"

# 4. Generate NEW secret key (don't reuse old one!)
railway variables set FLASK_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"

# 5. Set new app-specific variables
railway variables set FLASK_DEBUG=False
railway variables set SESSION_COOKIE_SECURE=True
railway variables set NO_SMS_MODE=False
railway variables set NO_EMAIL_MODE=True

# 6. Deploy
railway up
```

---

## 🔐 Security Note: Don't Share Secret Keys

**❌ DO NOT reuse FLASK_SECRET_KEY between apps!**

```bash
# Old app: Has its own secret key
# New app: Must generate NEW secret key

# Why:
# - If one app is compromised, both would be vulnerable
# - Session cookies would be interchangeable
# - Security best practice: one secret per app

# Generate unique key for new app:
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🌐 Domain Strategy Recommendations

### Strategy 1: Move Primary Domain to New App (Recommended)

**Setup:**
```
medalpool.com → New multi-contest app (OlympicPool2)
v1.medalpool.com → Old single-contest app
```

**Advantages:**
- Clean primary domain for new app
- Old app still accessible for existing users
- Clear distinction between versions

**Steps:**
1. Add v1.medalpool.com to old Railway project
2. Update DNS: v1 → old Railway app
3. Add medalpool.com to new Railway project
4. Update DNS: @ → new Railway app
5. Update BASE_URL in old app to https://v1.medalpool.com
6. Update BASE_URL in new app to https://medalpool.com

---

### Strategy 2: Use Subdomain for New App

**Setup:**
```
medalpool.com → Old single-contest app (unchanged)
app.medalpool.com → New multi-contest app (OlympicPool2)
```

**Advantages:**
- No disruption to current users
- Old app URL unchanged
- Easy rollback if needed

**Steps:**
1. Add app.medalpool.com to new Railway project
2. Update DNS: app → new Railway app
3. Wait for SSL provisioning
4. Update BASE_URL in new app to https://app.medalpool.com

**Variation Options:**
- multi.medalpool.com
- pool.medalpool.com
- contest.medalpool.com
- 2026.medalpool.com

---

## 📊 Monitoring Both Apps

### Railway Dashboard

**View both projects:**
```bash
railway projects
# Select project to view logs/metrics
```

**Or in Railway web dashboard:**
- All projects visible in left sidebar
- Click project name to switch
- Each has separate logs, metrics, deployments

### Twilio Dashboard

**Single dashboard shows activity from both apps:**
- Go to https://console.twilio.com/verify
- View all verification attempts
- Can't distinguish which app sent each SMS (they share the service)

**Tip:** Add different message templates if you want to distinguish:
- Old app: "Your MedalPool verification code is: {code}"
- New app: "Your OlympicPool verification code is: {code}"

---

## 🔄 Migration Path (Optional)

If you want to eventually migrate users from old app to new app:

### Phase 1: Run Both Apps (Months 1-2)
- Old app continues with existing contest
- New app starts fresh with Milano 2026
- No user migration yet

### Phase 2: Soft Migration (Months 2-3)
- Encourage users to join new app for Milano 2026
- Old app remains read-only after contest ends
- Users manually register on new app

### Phase 3: Data Migration (Optional)
- Export user data from old app database
- Import into new app database
- Map users to new contest structure

### Phase 4: Sunset Old App (Months 6-12)
- Archive old app data
- Redirect old domain to new app
- Shut down old Railway project

---

## 🎯 Recommended Approach

**For immediate deployment:**

1. **Create new Railway project** for OlympicPool2
2. **Reuse these credentials:**
   - ✅ Twilio Account SID
   - ✅ Twilio Auth Token
   - ✅ Twilio Verify Service SID
   - ✅ Resend API Key (if using)
   - ✅ Admin email addresses

3. **Create new infrastructure:**
   - ❌ Railway volume (new)
   - ❌ Database (new, empty)
   - ❌ Generate new FLASK_SECRET_KEY

4. **Domain strategy:**
   - **Option A:** Point medalpool.com to new app, old app to v1.medalpool.com
   - **Option B:** Point app.medalpool.com to new app, keep old app on medalpool.com

5. **Run both apps simultaneously:**
   - Old app: Existing users, existing contest(s)
   - New app: Fresh start, Milano 2026, new users
   - Decide migration path later

---

## 📝 Quick Copy-Paste: Reuse Credentials

```bash
# 1. Get credentials from old app
railway link  # Select old project
OLD_TWILIO_SID=$(railway variables get TWILIO_ACCOUNT_SID)
OLD_TWILIO_TOKEN=$(railway variables get TWILIO_AUTH_TOKEN)
OLD_TWILIO_SERVICE=$(railway variables get TWILIO_VERIFY_SERVICE_SID)
OLD_RESEND_KEY=$(railway variables get RESEND_API_KEY)
OLD_ADMIN_EMAILS=$(railway variables get ADMIN_EMAILS)

# 2. Switch to new project
cd /Users/kcorless/Documents/Projects/OlympicPool2
railway link  # Select new project

# 3. Set credentials in new project (reusing from old)
railway variables set TWILIO_ACCOUNT_SID="$OLD_TWILIO_SID"
railway variables set TWILIO_AUTH_TOKEN="$OLD_TWILIO_TOKEN"
railway variables set TWILIO_VERIFY_SERVICE_SID="$OLD_TWILIO_SERVICE"
railway variables set RESEND_API_KEY="$OLD_RESEND_KEY"
railway variables set ADMIN_EMAILS="$OLD_ADMIN_EMAILS"

# 4. Generate NEW secret key (don't reuse!)
railway variables set FLASK_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"

# 5. Set new app config
railway variables set FLASK_DEBUG=False
railway variables set SESSION_COOKIE_SECURE=True
railway variables set GLOBAL_ADMIN_EMAILS="$OLD_ADMIN_EMAILS"
railway variables set NO_SMS_MODE=False
railway variables set NO_EMAIL_MODE=True

# 6. Deploy
railway up
```

---

## Summary

### ✅ Reuse (No Extra Setup)
- Twilio account and credentials
- Resend API key
- Admin email addresses
- Railway account
- Domain registrar account

### ❌ Create New (Required)
- Railway project
- Railway volume
- SQLite database
- Flask secret key
- SSL certificate (auto)

### 💰 Cost Impact
- **With Developer Plan:** ~$0-5/month extra
- **With Hobby Plan:** ~$20/month extra (need second plan)

### 🚀 Recommended Path
1. Reuse Twilio credentials
2. Create new Railway project
3. Deploy new app to subdomain initially
4. Test thoroughly
5. Decide on domain strategy later
6. Run both apps until ready to migrate

---

**Questions? See DEPLOYMENT.md for full deployment guide.**
