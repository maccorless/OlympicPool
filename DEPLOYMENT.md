# Railway Deployment Guide - OlympicPool2

This guide walks you through deploying the OlympicPool2 application to Railway with custom domain medalpool.com.

## Prerequisites

- [ ] Railway account at https://railway.app
- [ ] Railway CLI installed: `npm install -g @railway/cli`
- [ ] Domain medalpool.com with DNS access
- [ ] Twilio account with Verify service configured
- [ ] (Optional) Resend API key for email

## Quick Start

### 1. Install Railway CLI

```bash
npm install -g @railway/cli
```

### 2. Login to Railway

```bash
railway login
```

### 3. Create New Project

From the project directory:

```bash
cd /Users/kcorless/Documents/Projects/OlympicPool2
railway init
```

When prompted:
- Project name: `olympic-medal-pool-multi`
- Environment: `production`

### 4. Create Database Volume

**Critical: Volume must be created before first deployment to persist database.**

```bash
# Create volume
railway volume add --mount-path /app/instance

# Verify volume created
railway volume list
```

Expected output:
```
NAME       MOUNT PATH      SIZE
database   /app/instance   1 GB
```

### 5. Set Environment Variables

#### Option A: Set via Railway Dashboard

1. Go to https://railway.app/dashboard
2. Select your project: `olympic-medal-pool-multi`
3. Click "Variables" tab
4. Add each variable from the list below

#### Option B: Set via CLI

**Generate a strong secret key first:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Set all required variables:**
```bash
# Core Configuration
railway variables set FLASK_SECRET_KEY="<generated-secret-key>"
railway variables set FLASK_DEBUG=False
railway variables set BASE_URL="https://olympic-medal-pool-multi-production.up.railway.app"

# Admin Access
railway variables set ADMIN_EMAILS="your@email.com"
railway variables set GLOBAL_ADMIN_EMAILS="your@email.com"

# Session Security (REQUIRED for HTTPS)
railway variables set SESSION_COOKIE_SECURE=True

# SMS Authentication (Twilio)
railway variables set TWILIO_ACCOUNT_SID="ACxxxxx"
railway variables set TWILIO_AUTH_TOKEN="xxxxx"
railway variables set TWILIO_VERIFY_SERVICE_SID="VAxxxxx"
railway variables set NO_SMS_MODE=False

# Email (Resend) - Optional
railway variables set RESEND_API_KEY="re_xxxxx"
railway variables set NO_EMAIL_MODE=True
```

**For testing without SMS (set NO_SMS_MODE=True):**
```bash
railway variables set NO_SMS_MODE=True
```

**Verify variables are set:**
```bash
railway variables
```

### 6. Deploy Application

#### Automatic Deployment (Recommended)

If you connected GitHub repository during `railway init`:

```bash
git add .
git commit -m "Configure for Railway deployment"
git push origin main
```

Railway automatically deploys on push to main branch.

#### Manual Deployment

```bash
railway up
```

### 7. Monitor Deployment

**Watch logs in real-time:**
```bash
railway logs --follow
```

**Expected output:**
```
Starting Olympic Medal Pool...
Database directory: /app/instance
Database not found at /app/instance/medal_pool.db. Initializing...
Running flask init-db...
Database initialized.
Loading countries...
58 countries loaded successfully.
Starting gunicorn...
[INFO] Listening at: http://0.0.0.0:8000
```

**Check deployment status:**
```bash
railway status
```

### 8. Get Railway URL

```bash
railway domain
```

Your app is now live at: `https://<project>.up.railway.app`

**Test the deployment:**
```bash
curl https://<project>.up.railway.app
```

## Custom Domain Setup (medalpool.com)

### 1. Add Domain to Railway

**Via Railway Dashboard:**
1. Go to project settings
2. Click "Domains" tab
3. Click "Custom Domain"
4. Enter: `medalpool.com`
5. Railway provides DNS records

**Via CLI:**
```bash
railway domain add medalpool.com
```

Railway will show the DNS records you need to configure.

### 2. Configure DNS

At your domain registrar (GoDaddy, Namecheap, Cloudflare, etc.):

**Option A: CNAME Record (Recommended)**
```
Type: CNAME
Name: @
Value: <your-project>.up.railway.app
TTL: 3600
```

**Option B: A Records**
```
Type: A
Name: @
Value: <railway-ip-address>
TTL: 3600
```

**Add www subdomain (optional):**
```
Type: CNAME
Name: www
Value: medalpool.com
TTL: 3600
```

### 3. Wait for DNS Propagation

Check DNS propagation:
```bash
dig medalpool.com
```

Typically takes 5-60 minutes.

### 4. Update BASE_URL

Once domain is active:

```bash
railway variables set BASE_URL="https://medalpool.com"
```

Railway will restart the app with the new BASE_URL.

### 5. Verify SSL

Visit https://medalpool.com - should show secure padlock.

Railway automatically provisions Let's Encrypt SSL certificate.

## Post-Deployment Setup

### 1. Access Global Admin

1. Visit https://medalpool.com/admin/global
2. Login with your admin email (configured in ADMIN_EMAILS)
3. You should see the Global Admin Dashboard

### 2. Create First Event

1. Click "Create New Event"
2. Fill in details:
   - Name: Milano Cortina 2026
   - Slug: milano-2026
   - Start Date: 2026-02-06
   - End Date: 2026-02-22
   - Active: Yes
3. Click "Create Event"

Countries should already be loaded from data/countries.sql during startup.

### 3. Create First Contest

1. From Global Admin, click "Create New Contest"
2. Fill in details:
   - Event: Milano Cortina 2026
   - Slug: main-pool
   - Name: Olympic Medal Pool 2026
   - Budget: 200
   - Max Countries: 10
   - Deadline: 2026-02-04T23:59:59
   - State: setup
3. Click "Create Contest"

### 4. Verify Contest URL

Contest should be accessible at:
```
https://medalpool.com/milano-2026/main-pool
```

## Testing Checklist

After deployment, verify:

**Basic Functionality:**
- [ ] Homepage loads (/)
- [ ] Contest selector shows events/contests
- [ ] Contest home loads (/<event>/<contest>)
- [ ] Registration form loads
- [ ] Login form loads
- [ ] Can register new user (SMS OTP sent/shown)
- [ ] Can login (SMS OTP verification works)
- [ ] Draft picker loads with countries
- [ ] Can submit picks
- [ ] My Picks page shows selections
- [ ] Leaderboard displays correctly

**Admin Functionality:**
- [ ] Global admin accessible (/admin/global)
- [ ] Can view/create/edit/delete events
- [ ] Can view/create/edit/delete contests
- [ ] Contest admin accessible (/<event>/<contest>/admin)
- [ ] Can view users
- [ ] Can update medals
- [ ] Countries already loaded

**Security:**
- [ ] HTTPS works (padlock shows)
- [ ] Session persists across requests
- [ ] Non-admin blocked from admin routes
- [ ] Session cookie is Secure (check DevTools)

## Database Management

### Backup Database

**Method 1: Via Railway Dashboard**
1. Project → Service
2. Click "Connect"
3. In terminal: `sqlite3 /app/instance/medal_pool.db .dump > backup.sql`
4. Download file

**Method 2: Via CLI**
```bash
railway run sqlite3 /app/instance/medal_pool.db .dump > backup-$(date +%Y%m%d).sql
```

### Restore Database

```bash
railway run bash
cd /app/instance
sqlite3 medal_pool.db < backup.sql
exit
```

### View Database

```bash
railway run bash
sqlite3 /app/instance/medal_pool.db
```

```sql
-- Check contests
SELECT * FROM contest;

-- Check events
SELECT * FROM events;

-- Check users
SELECT * FROM users;

-- Check picks
SELECT user_id, COUNT(*) as picks FROM picks GROUP BY user_id;

-- Exit
.quit
```

## Monitoring & Logs

### View Logs

**Real-time logs:**
```bash
railway logs --follow
```

**Recent logs:**
```bash
railway logs
```

**Via Dashboard:**
Project → Deployments → Click deployment → View logs

### Key Metrics

**Via Dashboard:**
Project → Metrics

Monitor:
- CPU usage
- Memory usage
- Network traffic
- Request count

## Troubleshooting

### Database Not Persisting

**Symptom:** Database resets on each deployment

**Solution:**
```bash
# Verify volume exists and is mounted
railway volume list

# Should show:
# NAME       MOUNT PATH      SIZE
# database   /app/instance   1 GB

# If missing, create it:
railway volume add --mount-path /app/instance

# Redeploy
railway up
```

### SMS Not Sending

**Symptom:** Users not receiving SMS codes

**Solution:**
```bash
# Verify Twilio credentials
railway variables | grep TWILIO

# Test with NO_SMS_MODE temporarily
railway variables set NO_SMS_MODE=True

# Check logs for Twilio errors
railway logs | grep -i twilio
```

### SSL Not Working

**Symptom:** https://medalpool.com shows certificate error

**Solution:**
1. Verify DNS is pointing to Railway: `dig medalpool.com`
2. Wait 10-15 minutes for Let's Encrypt provisioning
3. Check Railway dashboard → Domains → Status should be "Active"
4. If stuck, remove and re-add custom domain

### Environment Variables Not Loading

**Symptom:** App uses default values

**Solution:**
```bash
# List all variables
railway variables

# Check for typos in variable names
# Restart service
railway restart

# Check logs for .env messages
railway logs | grep -i env
```

### 502 Bad Gateway

**Symptom:** Railway shows 502 error

**Solution:**
```bash
# Check logs for startup errors
railway logs

# Common issues:
# - Missing dependencies in requirements.txt
# - Database initialization failure
# - Port binding issues

# Redeploy
railway up
```

## Railway CLI Cheat Sheet

```bash
# Login
railway login

# Create project
railway init

# Deploy
railway up

# View logs
railway logs
railway logs --follow

# Environment variables
railway variables
railway variables set KEY=value
railway variables delete KEY

# Domain management
railway domain
railway domain add medalpool.com

# Volume management
railway volume list
railway volume create <name> --mount-path <path>

# Run commands in production
railway run <command>
railway run bash

# Project info
railway status
railway whoami

# Restart service
railway restart

# Open in browser
railway open
```

## Cost Estimate

**Railway Pricing:**
- Hobby Plan: $5/month (500 execution hours)
- Developer Plan: $20/month (unlimited execution hours)

**Recommended:** Developer Plan ($20/month) for always-on service

**Volume Storage:**
- 1GB volume: Included
- Additional storage: $0.25/GB/month

**Expected Monthly Cost:** $20-25/month

## Rollback Plan

### Rollback to Previous Deployment

```bash
railway rollback
```

### Rollback to Specific Commit

```bash
git checkout <previous-commit-hash>
railway up
```

### Switch DNS to Old App (Emergency)

If critical issues:
1. Update DNS to point to old Railway project
2. Gives time to fix new deployment
3. Users continue on old app

## Production Checklist

Before going live with real users:

**Configuration:**
- [ ] `FLASK_DEBUG=False`
- [ ] `SESSION_COOKIE_SECURE=True`
- [ ] Strong `FLASK_SECRET_KEY` (32+ characters)
- [ ] Correct `BASE_URL` (https://medalpool.com)
- [ ] Admin emails configured
- [ ] Twilio credentials configured

**Database:**
- [ ] Volume mounted at `/app/instance`
- [ ] Database initialized with schema
- [ ] Countries loaded
- [ ] Test backup/restore process

**Domain:**
- [ ] DNS pointing to Railway
- [ ] SSL certificate active
- [ ] Domain shows "Active" in Railway

**Testing:**
- [ ] Complete end-to-end user flow
- [ ] Admin functions work
- [ ] Session persists
- [ ] No errors in logs

**Monitoring:**
- [ ] Bookmark Railway dashboard
- [ ] Set up log monitoring
- [ ] Document admin access

## Support

**Railway Documentation:** https://docs.railway.app
**Railway Discord:** https://discord.gg/railway
**Project Issues:** https://github.com/anthropics/claude-code/issues

## Next Steps

1. Complete this deployment checklist
2. Test all functionality
3. Create first event and contest via Global Admin
4. Set contest state to "open" when ready
5. Share contest URL with users
6. Monitor logs and metrics
7. Set up regular database backups

Good luck with your deployment! 🚀
