# Pre-Deployment Checklist

Complete this checklist before deploying OlympicPool2 to Railway.

## 📋 Prerequisites

### Railway Account & CLI

- [ ] Railway account created at https://railway.app
- [ ] Railway CLI installed: `npm install -g @railway/cli`
- [ ] Railway CLI working: `railway --version`
- [ ] Logged into Railway CLI: `railway login`

### Domain & DNS (If using custom domain)

- [ ] Domain medalpool.com registered
- [ ] Access to domain DNS settings
- [ ] DNS registrar account login ready

### Third-Party Services

#### Twilio (Required for SMS OTP)

- [ ] Twilio account created at https://www.twilio.com
- [ ] Twilio Verify service created
- [ ] Have Twilio Account SID
- [ ] Have Twilio Auth Token
- [ ] Have Twilio Verify Service SID
- [ ] Tested Twilio Verify with test phone number

**Or:**

- [ ] Plan to use `NO_SMS_MODE=True` for testing (shows OTP on page)

#### Resend (Optional for email)

- [ ] Resend account created at https://resend.com (or skip if not using email)
- [ ] Resend API key generated (or skip)
- [ ] Or plan to use `NO_EMAIL_MODE=True`

## 🔧 Local Environment

### Code Readiness

- [ ] All code changes committed to git
- [ ] Working directory is clean: `git status`
- [ ] On correct branch (main or deployment branch)
- [ ] All tests passing: `pytest` (if tests exist)
- [ ] No errors when running locally: `flask run`

### Configuration Files

- [ ] `Dockerfile` exists and is correct
- [ ] `railway.toml` exists and is correct
- [ ] `start.sh` exists and is executable
- [ ] `requirements.txt` is complete and up-to-date
- [ ] `schema.sql` exists and is correct
- [ ] `data/countries.sql` exists and has data
- [ ] `.env.example` is up-to-date

### Local Testing

- [ ] App runs locally: `flask run`
- [ ] Database initializes: `flask init-db`
- [ ] Countries load: `flask load-countries`
- [ ] Can register new user
- [ ] Can login with SMS OTP (or NO_SMS_MODE)
- [ ] Can create picks
- [ ] Leaderboard displays correctly
- [ ] Admin routes accessible

## 🔐 Security

### Credentials Prepared

- [ ] Strong Flask secret key generated (32+ characters)
  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- [ ] Admin email addresses determined
- [ ] Global admin email addresses determined
- [ ] Twilio credentials ready (Account SID, Auth Token, Service SID)
- [ ] Resend API key ready (or skipping email)

### Security Settings

- [ ] Will set `FLASK_DEBUG=False` in production
- [ ] Will set `SESSION_COOKIE_SECURE=True` in production
- [ ] Will use HTTPS only (no HTTP)
- [ ] Will not commit secrets to git

## 🗄️ Database

### Schema & Data

- [ ] `schema.sql` is finalized
- [ ] All migrations applied (if any)
- [ ] `data/countries.sql` has all countries
- [ ] Countries data is accurate (costs, codes, names)
- [ ] No test/dummy data in country list

### Backup Plan

- [ ] Understand how to backup Railway database
- [ ] Have backup script ready
- [ ] Tested backup/restore locally
- [ ] Plan for regular backups (weekly minimum)

## 🚀 Deployment Configuration

### Railway Project

- [ ] Railway project name decided: `olympic-medal-pool-multi`
- [ ] Environment selected: `production`
- [ ] Region selected (or using default)

### Volume Configuration

- [ ] Understand volume is required for database persistence
- [ ] Plan to create volume: `database`
- [ ] Plan to mount at: `/app/instance`
- [ ] Volume size: 1GB (or larger if needed)

### Environment Variables

Prepare these values:

```bash
# Core
FLASK_SECRET_KEY=<generated-secret>
FLASK_DEBUG=False
BASE_URL=<will-be-set-after-deployment>

# Admin
ADMIN_EMAILS=<your-email>
GLOBAL_ADMIN_EMAILS=<your-email>

# Security
SESSION_COOKIE_SECURE=True

# SMS (Twilio)
TWILIO_ACCOUNT_SID=<your-sid>
TWILIO_AUTH_TOKEN=<your-token>
TWILIO_VERIFY_SERVICE_SID=<your-service-sid>
NO_SMS_MODE=False

# Email (Resend) - Optional
RESEND_API_KEY=<your-key>
NO_EMAIL_MODE=True
```

- [ ] All values prepared
- [ ] Values tested locally
- [ ] No secrets in git

## 📡 Domain & SSL (If using custom domain)

### DNS Configuration

- [ ] Understand DNS propagation takes 5-60 minutes
- [ ] Know how to add CNAME record at registrar
- [ ] Know how to check DNS: `dig medalpool.com`

### SSL Certificate

- [ ] Understand Railway auto-provisions Let's Encrypt SSL
- [ ] No manual SSL configuration needed
- [ ] SSL will activate after DNS propagation

## 📊 Monitoring & Logging

### Setup

- [ ] Bookmark Railway dashboard URL
- [ ] Know how to view logs: `railway logs --follow`
- [ ] Understand metrics in Railway dashboard
- [ ] Plan to monitor logs for first 24 hours

### Alerting (Optional)

- [ ] Consider setting up Railway alerts
- [ ] Consider external monitoring (Uptime Robot, etc.)

## 🧪 Testing Plan

### Post-Deployment Tests

Plan to test these immediately after deployment:

- [ ] Homepage loads
- [ ] Contest selector works
- [ ] Registration flow works
- [ ] Login with SMS OTP works
- [ ] Draft picker loads
- [ ] Can submit picks
- [ ] My Picks page works
- [ ] Leaderboard displays
- [ ] Global admin accessible
- [ ] Contest admin accessible
- [ ] Can create event
- [ ] Can create contest
- [ ] Database persists after redeployment

### User Acceptance Testing

- [ ] Have test users ready
- [ ] Plan to test full user flow
- [ ] Plan to test on mobile devices
- [ ] Plan to test in multiple browsers

## 💰 Cost & Budget

### Railway Pricing

- [ ] Understand Railway pricing tiers
- [ ] Selected plan: Hobby ($5/mo) or Developer ($20/mo)
- [ ] Understand volume storage costs ($0.25/GB/month)
- [ ] Estimated monthly cost: $20-25/month
- [ ] Budget approved

### Usage Monitoring

- [ ] Plan to monitor Railway usage
- [ ] Set up cost alerts (if available)
- [ ] Understand execution hours limit (if on Hobby plan)

## 📱 Communication

### Stakeholders

- [ ] Informed stakeholders of deployment schedule
- [ ] Scheduled deployment window
- [ ] Have rollback plan communicated
- [ ] Support contacts identified

### Users

- [ ] Plan for user communication (if existing users)
- [ ] Maintenance notice prepared (if needed)
- [ ] Contest URLs will be shared after verification

## 🔄 Rollback Plan

### Preparation

- [ ] Understand rollback command: `railway rollback`
- [ ] Have previous working version identified
- [ ] Can switch DNS to old app if needed
- [ ] Have emergency contacts ready

### Criteria

- [ ] Defined what constitutes a failed deployment
- [ ] Defined rollback decision timeline
- [ ] Know who can authorize rollback

## 📚 Documentation

### Deployment Docs

- [ ] Read `DEPLOYMENT.md` fully
- [ ] Read `RAILWAY_QUICKREF.md`
- [ ] Understand deployment helper script
- [ ] Bookmarked Railway documentation

### App Documentation

- [ ] `CLAUDE.md` is up-to-date
- [ ] `README.md` has deployment info
- [ ] Environment variables documented
- [ ] Admin access documented

## ⏰ Deployment Day

### Timing

- [ ] Selected low-traffic time for deployment
- [ ] Allocated 1-2 hours for deployment
- [ ] Have backup time if issues arise
- [ ] Not deploying before major event/deadline

### Preparation

- [ ] Laptop fully charged (or plugged in)
- [ ] Stable internet connection
- [ ] No distractions planned
- [ ] Coffee/water ready ☕

### Team

- [ ] Technical support available
- [ ] Admin access to all services
- [ ] Backup person identified (if available)

## ✅ Final Checks

### Code

- [ ] Latest code committed and pushed
- [ ] No uncommitted changes: `git status`
- [ ] Branch up-to-date with remote: `git pull`

### Services

- [ ] Railway account accessible
- [ ] Twilio account accessible
- [ ] Resend account accessible (if using)
- [ ] Domain registrar accessible (if using custom domain)

### Mental Readiness

- [ ] Read deployment guide
- [ ] Understand each step
- [ ] Know where to get help
- [ ] Feeling confident (or at least prepared!)

## 🎯 Post-Deployment

After successful deployment:

- [ ] Monitor logs for 30 minutes
- [ ] Test all critical flows
- [ ] Verify database persistence
- [ ] Check SSL certificate
- [ ] Send test SMS OTP
- [ ] Create test user account
- [ ] Submit test picks
- [ ] View test leaderboard
- [ ] Access admin panels
- [ ] Take first database backup
- [ ] Document any issues encountered
- [ ] Update documentation if needed
- [ ] Celebrate! 🎉

## 🆘 Emergency Contacts

Prepare these before deployment:

- Railway Support: https://help.railway.app
- Railway Discord: https://discord.gg/railway
- Twilio Support: https://support.twilio.com
- Domain Registrar Support: <your-registrar>

## 📝 Notes

Use this space for deployment-specific notes:

```
Deployment Date: _______________
Deployed By: _______________
Railway Project ID: _______________
Railway URL: _______________
Custom Domain: _______________
Issues Encountered:







Resolution:







```

---

## Quick Reference Commands

```bash
# Login to Railway
railway login

# Initialize project
railway init

# Create volume
railway volume add --mount-path /app/instance

# Set environment variable
railway variables set KEY=value

# Deploy
railway up

# View logs
railway logs --follow

# Check status
railway status

# Add custom domain
railway domain add medalpool.com

# Rollback
railway rollback
```

---

**When you've checked all boxes above, you're ready to deploy!**

Run the deployment helper script:
```bash
./deploy-to-railway.sh
```

Or follow the manual steps in `DEPLOYMENT.md`.

Good luck! 🚀
