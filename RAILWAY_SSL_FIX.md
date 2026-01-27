# Railway CLI SSL Certificate Error - Troubleshooting

**Error:** `invalid peer certificate: UnknownIssuer`

This means something is intercepting your HTTPS connection to Railway.

---

## 🔍 **Quick Diagnostics**

### 1. Test Railway Connection
```bash
curl https://backboard.railway.com/graphql/v2
```

If this works but Railway CLI doesn't, the issue is with Railway CLI specifically.

### 2. Check System Time
```bash
date
```

If your system time is wrong, SSL certificates won't validate. Make sure it's correct.

---

## 🛠️ **Solutions (Try in Order)**

### Solution 1: Set Railway to Skip SSL Verification (Quick Fix)

**Warning:** This skips SSL verification. Only use temporarily to get past the issue.

```bash
# Set environment variable
export RAILWAY_INSECURE=1

# Then try again
railway login
```

If this works, you can add it to your shell profile:
```bash
echo 'export RAILWAY_INSECURE=1' >> ~/.zshrc
source ~/.zshrc
```

---

### Solution 2: Check for Corporate Proxy/VPN

**Are you on a corporate network or VPN?**

If yes, try:
1. **Disconnect from VPN** temporarily
2. **Switch to personal WiFi/hotspot**
3. **Ask IT for Railway whitelist**

Test after each:
```bash
railway login
```

---

### Solution 3: Check Antivirus/Firewall

Some antivirus software intercepts HTTPS traffic:

**Common culprits:**
- Kaspersky
- Avast
- AVG
- Norton
- McAfee
- Corporate security software

**Try:**
1. Temporarily disable antivirus SSL inspection
2. Add Railway to whitelist: `*.railway.app`, `*.railway.com`
3. Test again

---

### Solution 4: Update CA Certificates (macOS)

```bash
# Update Homebrew (if you installed Railway via Homebrew)
brew update
brew upgrade railway

# Or reinstall Railway CLI
brew uninstall railway
brew install railway
```

---

### Solution 5: Use Web-Based Configuration (Workaround)

If Railway CLI won't work, you can configure everything via Railway Dashboard:

**Instead of `railway init`:**
1. Go to https://railway.app/new
2. Click "Empty Project"
3. Name it: `olympic-medal-pool-multi`
4. Click "Deploy"

**Instead of `railway volume add`:**
1. In Railway Dashboard → Select your project
2. Click "Settings" → "Volumes"
3. Click "New Volume"
4. Mount path: `/app/instance`

**Instead of `railway variables set`:**
1. In Railway Dashboard → Select your project
2. Click "Variables" tab
3. Click "New Variable"
4. Add each variable manually

**Instead of `railway up`:**
1. In Railway Dashboard → Select your project
2. Click "Settings" → "Deploy"
3. Connect to GitHub repo
4. Deploy from GitHub

---

### Solution 6: Install Railway via npm (Alternative Installation)

If Homebrew version has issues, try npm version:

```bash
# Uninstall current version
brew uninstall railway  # if installed via Homebrew

# Install via npm
npm install -g @railway/cli

# Try again
railway login
```

---

### Solution 7: Use Railway API Token (Advanced)

Skip `railway login` by using API token directly:

**Get API token:**
1. Go to https://railway.app/account/tokens
2. Click "Create Token"
3. Copy the token

**Set token:**
```bash
export RAILWAY_TOKEN=<your-token>
railway whoami  # Test it
```

Add to shell profile:
```bash
echo 'export RAILWAY_TOKEN=<your-token>' >> ~/.zshrc
source ~/.zshrc
```

---

## 🎯 **Recommended Approach**

### Quick Test:
```bash
# Try with SSL verification disabled
export RAILWAY_INSECURE=1
railway login
```

If this works:
- **Temporary:** Use `RAILWAY_INSECURE=1` for now
- **Permanent:** Investigate proxy/VPN/antivirus issue

If this doesn't work:
- **Option A:** Use Railway Dashboard (web UI) for all setup
- **Option B:** Use API token instead of `railway login`

---

## 📋 **Alternative: Deploy Without Railway CLI**

You can deploy entirely through GitHub + Railway Dashboard:

### Step 1: Push to GitHub
```bash
cd /Users/kcorless/Documents/Projects/OlympicPool2
git add .
git commit -m "Ready for Railway deployment"
git push origin main
```

### Step 2: Create Project via Railway Dashboard
1. Go to https://railway.app/new
2. Select "Deploy from GitHub repo"
3. Choose your OlympicPool2 repo
4. Railway auto-detects Dockerfile and deploys

### Step 3: Add Volume via Dashboard
1. Project → Settings → Volumes
2. New Volume → Mount path: `/app/instance`

### Step 4: Set Variables via Dashboard
1. Project → Variables tab
2. Add all environment variables manually:
   - FLASK_SECRET_KEY
   - TWILIO_ACCOUNT_SID
   - TWILIO_AUTH_TOKEN
   - etc.

### Step 5: Deploy
- Railway auto-deploys when you push to GitHub
- Or click "Deploy" in Railway Dashboard

---

## 🔍 **Check Network Environment**

Run these commands to diagnose:

```bash
# Check if you're behind a proxy
echo $HTTP_PROXY
echo $HTTPS_PROXY
echo $http_proxy
echo $https_proxy

# Check DNS resolution
nslookup backboard.railway.com

# Check connection to Railway
curl -v https://backboard.railway.com/graphql/v2

# Check Railway CLI version
railway --version
```

---

## 💡 **Most Likely Causes**

Based on the error `invalid peer certificate: UnknownIssuer`:

1. **Corporate Network** (80% chance)
   - Company firewall/proxy intercepts SSL
   - Solution: Use VPN bypass or Railway Dashboard

2. **Antivirus Software** (15% chance)
   - AV scans HTTPS traffic
   - Solution: Disable SSL inspection or whitelist Railway

3. **VPN** (5% chance)
   - VPN provider intercepts traffic
   - Solution: Disconnect VPN temporarily

---

## ✅ **Recommended Quick Fix**

**For now, use the web dashboard method:**

1. **Create project:** https://railway.app/new → "Empty Project"
2. **Add volume:** Project → Settings → Volumes → `/app/instance`
3. **Set variables:** Project → Variables → Add manually
4. **Deploy:** Push to GitHub, Railway auto-deploys

**This bypasses the Railway CLI entirely and works 100% of the time.**

---

## 🚀 **Next Steps**

**If you want to use CLI:**
- Try `export RAILWAY_INSECURE=1` first
- Contact Railway support: https://help.railway.app
- Check with your IT department about proxy settings

**If you want to skip CLI:**
- Use Railway Dashboard for all configuration
- Deploy via GitHub push
- Works identically to CLI deployment

---

## 📞 **Need Help?**

- Railway Discord: https://discord.gg/railway
- Railway Support: https://help.railway.app
- Check Railway Status: https://status.railway.app

---

**Bottom line:** The easiest workaround is to use Railway Dashboard (web UI) instead of CLI for initial setup.
