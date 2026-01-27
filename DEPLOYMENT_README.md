# Railway Deployment - Quick Start Guide

This guide provides a quick overview of deploying OlympicPool2 to Railway. For detailed instructions, see `DEPLOYMENT.md`.

## 📚 Documentation Files

- **DEPLOYMENT.md** - Complete deployment guide (step-by-step)
- **PRE_DEPLOYMENT_CHECKLIST.md** - Pre-flight checklist
- **RAILWAY_QUICKREF.md** - Railway CLI command reference
- **deploy-to-railway.sh** - Interactive deployment helper script
- **verify-deployment.sh** - Post-deployment verification script

## ⚡ Quick Start (5 Steps)

### 1. Prerequisites

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login
```

**You need:**
- Railway account
- Twilio account (for SMS OTP)
- Domain access (if using custom domain)

### 2. Run Deployment Helper

```bash
# From project directory
cd /Users/kcorless/Documents/Projects/OlympicPool2

# Run interactive deployment script
./deploy-to-railway.sh
```

The script will guide you through:
- Creating Railway project
- Setting up database volume
- Configuring environment variables
- Deploying the application

### 3. Verify Deployment

```bash
# Run verification script
./verify-deployment.sh
```

This tests:
- Application health
- Database persistence
- Environment configuration
- SSL certificate
- Route accessibility

### 4. Configure Custom Domain (Optional)

```bash
# Add domain to Railway
railway domain add medalpool.com

# Configure DNS at your registrar:
# CNAME: @ → <your-project>.up.railway.app

# Update BASE_URL
railway variables set BASE_URL="https://medalpool.com"
```

### 5. Initialize Application

1. Visit your Railway URL or custom domain
2. Access Global Admin: `/admin/global`
3. Create first event (Milano Cortina 2026)
4. Create first contest
5. Set contest state to "open"
6. Share contest URL with users

## 🎯 Manual Deployment (For Advanced Users)

If you prefer manual control:

```bash
# 1. Initialize project
railway init

# 2. Create volume
railway volume add --mount-path /app/instance

# 3. Set environment variables
railway variables set FLASK_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
railway variables set FLASK_DEBUG=False
railway variables set SESSION_COOKIE_SECURE=True
railway variables set ADMIN_EMAILS="your@email.com"
railway variables set GLOBAL_ADMIN_EMAILS="your@email.com"
railway variables set TWILIO_ACCOUNT_SID="ACxxxxx"
railway variables set TWILIO_AUTH_TOKEN="xxxxx"
railway variables set TWILIO_VERIFY_SERVICE_SID="VAxxxxx"
railway variables set NO_SMS_MODE=False

# 4. Deploy
railway up

# 5. Monitor
railway logs --follow
```

## 🔑 Required Environment Variables

### Core Configuration
```bash
FLASK_SECRET_KEY=<32+ character secret>
FLASK_DEBUG=False
BASE_URL=<your-railway-url>
SESSION_COOKIE_SECURE=True
```

### Admin Access
```bash
ADMIN_EMAILS=your@email.com
GLOBAL_ADMIN_EMAILS=your@email.com
```

### SMS Authentication (Twilio)
```bash
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=xxxxx
TWILIO_VERIFY_SERVICE_SID=VAxxxxx
NO_SMS_MODE=False
```

### Email (Optional)
```bash
RESEND_API_KEY=re_xxxxx
NO_EMAIL_MODE=True
```

**Generate secret key:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Railway Platform                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────┐     │
│  │  Docker Container                             │     │
│  │  ┌──────────────────────────────────┐        │     │
│  │  │  Gunicorn (WSGI Server)          │        │     │
│  │  │  ┌────────────────────────────┐  │        │     │
│  │  │  │  Flask App                 │  │        │     │
│  │  │  │  (OlympicPool2)            │  │        │     │
│  │  │  └────────────────────────────┘  │        │     │
│  │  └──────────────────────────────────┘        │     │
│  │                                               │     │
│  │  ┌──────────────────────────────────┐        │     │
│  │  │  Railway Volume                  │        │     │
│  │  │  Mount: /app/instance            │        │     │
│  │  │  ┌────────────────────────────┐  │        │     │
│  │  │  │  medal_pool.db (SQLite)    │  │        │     │
│  │  │  └────────────────────────────┘  │        │     │
│  │  └──────────────────────────────────┘        │     │
│  └──────────────────────────────────────────────┘     │
│                                                         │
│  ┌──────────────────────────────────────────────┐     │
│  │  Environment Variables                        │     │
│  │  - FLASK_SECRET_KEY                           │     │
│  │  - DATABASE_DIR=/app/instance                 │     │
│  │  - TWILIO_* (SMS OTP)                         │     │
│  │  - ADMIN_EMAILS                               │     │
│  └──────────────────────────────────────────────┘     │
│                                                         │
└─────────────────────────────────────────────────────────┘
            │
            │ HTTPS
            ▼
    ┌───────────────┐
    │  Railway CDN  │
    │  (SSL/HTTPS)  │
    └───────────────┘
            │
            │ Custom Domain (Optional)
            ▼
    medalpool.com
```

## 🔍 Verification Checklist

After deployment, verify:

**Application:**
- [ ] Homepage loads
- [ ] Registration works (SMS OTP sent)
- [ ] Login works (SMS OTP verification)
- [ ] Draft picker loads with countries
- [ ] Can submit picks
- [ ] Leaderboard displays

**Admin:**
- [ ] Global admin accessible
- [ ] Contest admin accessible
- [ ] Can create events
- [ ] Can create contests

**Infrastructure:**
- [ ] SSL certificate active
- [ ] Database persists after redeployment
- [ ] Volume mounted correctly
- [ ] Environment variables loaded
- [ ] No errors in logs

**Security:**
- [ ] FLASK_DEBUG=False
- [ ] SESSION_COOKIE_SECURE=True
- [ ] Strong secret key in use
- [ ] Admin emails configured

## 🚨 Troubleshooting

### Database Not Persisting

```bash
# Check volume
railway volume list

# Should show:
# NAME       MOUNT PATH      SIZE
# database   /app/instance   1 GB

# If missing, create it:
railway volume add --mount-path /app/instance
railway up
```

### SMS Not Sending

```bash
# Verify Twilio credentials
railway variables | grep TWILIO

# Test without SMS temporarily
railway variables set NO_SMS_MODE=True
```

### App Not Starting

```bash
# Check logs
railway logs --follow

# Check status
railway status

# Restart
railway restart
```

### SSL Certificate Issues

```bash
# Verify domain
railway domain

# Check DNS
dig medalpool.com

# Wait 10-15 minutes for Let's Encrypt provisioning
```

## 📈 Monitoring

### View Logs
```bash
# Real-time logs
railway logs --follow

# Recent logs
railway logs

# Filter by time
railway logs --since 1h
```

### Check Status
```bash
# Service status
railway status

# View metrics (in dashboard)
railway open
```

### Database Backup
```bash
# Create backup
railway run sqlite3 /app/instance/medal_pool.db .dump > backup-$(date +%Y%m%d).sql

# Restore backup
railway run bash
sqlite3 /app/instance/medal_pool.db < backup.sql
exit
```

## 💡 Common Commands

```bash
# Deploy changes
railway up

# View logs
railway logs --follow

# List environment variables
railway variables

# Set variable
railway variables set KEY=value

# Add custom domain
railway domain add medalpool.com

# Restart service
railway restart

# Rollback deployment
railway rollback

# Run command in production
railway run <command>

# Open Railway dashboard
railway open
```

## 📞 Support

**Railway:**
- Documentation: https://docs.railway.app
- Discord: https://discord.gg/railway
- Status: https://status.railway.app

**Project:**
- Deployment Guide: `DEPLOYMENT.md`
- CLI Reference: `RAILWAY_QUICKREF.md`
- Pre-flight Checklist: `PRE_DEPLOYMENT_CHECKLIST.md`

## 🎉 Success Criteria

Deployment is successful when:
- ✅ App accessible at Railway URL
- ✅ SSL certificate active
- ✅ Database persists across deployments
- ✅ Users can register and login (SMS OTP)
- ✅ Draft picker works
- ✅ Leaderboard displays
- ✅ Admin panels accessible
- ✅ No errors in logs

## 🚀 Next Steps

After successful deployment:

1. **Test thoroughly** - Complete user flow end-to-end
2. **Create event** - Via Global Admin
3. **Create contest** - Via Global Admin
4. **Backup database** - Set up regular backups
5. **Monitor logs** - Check for errors daily
6. **Share URL** - With users when ready

## 💰 Cost Estimate

**Railway Pricing:**
- Developer Plan: $20/month (recommended)
- 1GB Volume: Included
- Bandwidth: 100GB/month included

**Expected:** $20-25/month for production deployment

## 📝 Deployment Timeline

**First-time deployment:**
- Setup & configuration: 15-30 minutes
- Deployment & verification: 10-15 minutes
- Custom domain setup: 10-60 minutes (DNS propagation)
- **Total: 35-105 minutes**

**Subsequent deployments:**
- Push to main branch: Automatic (2-5 minutes)
- Manual deployment: `railway up` (2-5 minutes)

## ✅ Pre-Deployment Checklist (Summary)

Before deploying:
- [ ] Railway CLI installed and logged in
- [ ] Twilio account configured
- [ ] Admin email addresses ready
- [ ] Strong secret key generated
- [ ] All code committed to git
- [ ] Tests passing locally
- [ ] Read deployment documentation

Ready to deploy? Run:
```bash
./deploy-to-railway.sh
```

---

**Good luck with your deployment!** 🚀

For detailed step-by-step instructions, see `DEPLOYMENT.md`.
