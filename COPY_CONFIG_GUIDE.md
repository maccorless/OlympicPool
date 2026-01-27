# Configuration Copy Guide - Old App → New App

**Good news! You can copy MOST variables from your old Railway project.** This saves time and reduces typing errors.

---

## ✅ **Variables You CAN Copy (Reuse)**

These variables can be safely copied from your old app to your new app:

### 1. **Twilio Credentials** ✅ COPY
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_VERIFY_SERVICE_SID=VAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
**Why safe to copy:** Same Twilio account works for multiple apps

---

### 2. **Resend API Key** ✅ COPY (if using)
```bash
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxx
```
**Why safe to copy:** Same Resend account works for multiple apps

---

### 3. **Admin Emails** ✅ COPY
```bash
ADMIN_EMAILS=your@email.com,other@email.com
GLOBAL_ADMIN_EMAILS=your@email.com
```
**Why safe to copy:** You're the admin of both apps

---

### 4. **Configuration Flags** ✅ COPY
```bash
FLASK_DEBUG=False
SESSION_COOKIE_SECURE=True
NO_SMS_MODE=False
NO_EMAIL_MODE=True
```
**Why safe to copy:** Same production settings for both apps

---

## ❌ **Variables You MUST Change (Don't Copy)**

### 1. **FLASK_SECRET_KEY** ❌ GENERATE NEW
```bash
# Old app: Has its own secret
FLASK_SECRET_KEY=old-secret-key-xxxxxx

# New app: MUST generate NEW secret
FLASK_SECRET_KEY=new-secret-key-yyyyyy
```

**Why must be different:**
- Security best practice
- Each app needs unique secret
- If one app compromised, both would be vulnerable
- Session cookies would be interchangeable (security risk)

**How to generate:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

### 2. **BASE_URL** ❌ DIFFERENT URL
```bash
# Old app
BASE_URL=https://your-old-project.up.railway.app
# or: https://medalpool.com

# New app
BASE_URL=https://your-new-project.up.railway.app
# or: https://app.medalpool.com
```

**Why must be different:**
- Each app has different Railway URL
- Each app may have different custom domain
- Set after deployment when you know the URL

---

## 🤖 **Automated Copy Script**

**Easiest method: Use the automated script**

```bash
./copy-railway-config.sh
```

**What it does:**
1. Prompts you to select old project
2. Fetches all variables from old project
3. Prompts you to select/create new project
4. Copies safe variables to new project
5. Generates new FLASK_SECRET_KEY
6. Sets production defaults
7. Shows summary of what was copied

**Time saved:** ~5-10 minutes vs manual entry

---

## 📋 **Manual Copy Method**

If you prefer to copy manually:

### Step 1: View Old Project Variables
```bash
# Link to old project
cd /path/to/old/project  # Your old app directory
railway link  # Select old project

# View all variables
railway variables

# Or get specific variable
railway variables get TWILIO_ACCOUNT_SID
```

### Step 2: Copy Variables You Need
Write down or copy these values:
- [ ] TWILIO_ACCOUNT_SID
- [ ] TWILIO_AUTH_TOKEN
- [ ] TWILIO_VERIFY_SERVICE_SID
- [ ] RESEND_API_KEY (if using)
- [ ] ADMIN_EMAILS
- [ ] GLOBAL_ADMIN_EMAILS

### Step 3: Generate New Secret Key
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Save this output
```

### Step 4: Switch to New Project
```bash
cd /Users/kcorless/Documents/Projects/OlympicPool2
railway link  # Select new project (or railway init if not created)
```

### Step 5: Set Variables in New Project
```bash
# Copy these from old app
railway variables set TWILIO_ACCOUNT_SID="<copied-value>"
railway variables set TWILIO_AUTH_TOKEN="<copied-value>"
railway variables set TWILIO_VERIFY_SERVICE_SID="<copied-value>"
railway variables set RESEND_API_KEY="<copied-value>"  # if using
railway variables set ADMIN_EMAILS="<copied-emails>"
railway variables set GLOBAL_ADMIN_EMAILS="<copied-emails>"

# Generate NEW secret (don't copy from old!)
railway variables set FLASK_SECRET_KEY="<newly-generated-secret>"

# Production settings (same for both apps)
railway variables set FLASK_DEBUG=False
railway variables set SESSION_COOKIE_SECURE=True
railway variables set NO_SMS_MODE=False
railway variables set NO_EMAIL_MODE=True

# BASE_URL - set after deployment
# railway variables set BASE_URL="<will-set-later>"
```

---

## 🔍 **Quick Copy Reference Table**

| Variable | Copy from Old? | Notes |
|----------|---------------|-------|
| **TWILIO_ACCOUNT_SID** | ✅ YES | Same account for both apps |
| **TWILIO_AUTH_TOKEN** | ✅ YES | Same account for both apps |
| **TWILIO_VERIFY_SERVICE_SID** | ✅ YES | Same service for both apps |
| **RESEND_API_KEY** | ✅ YES | Optional, if using email |
| **ADMIN_EMAILS** | ✅ YES | Same admin(s) for both apps |
| **GLOBAL_ADMIN_EMAILS** | ✅ YES | Same admin(s) for both apps |
| **FLASK_DEBUG** | ✅ YES | False for both (production) |
| **SESSION_COOKIE_SECURE** | ✅ YES | True for both (HTTPS) |
| **NO_SMS_MODE** | ✅ YES | Same setting for both |
| **NO_EMAIL_MODE** | ✅ YES | Same setting for both |
| **FLASK_SECRET_KEY** | ❌ NO | **MUST generate new** |
| **BASE_URL** | ❌ NO | Different URL for each app |
| **DATABASE_DIR** | ✅ YES | /app/instance for both |

---

## 💡 **Pro Tips**

### Tip 1: Use the Automated Script
**Fastest method:**
```bash
./copy-railway-config.sh
```
Handles everything automatically.

### Tip 2: Save Variables to File (Manual Method)
```bash
# In old project
railway variables > old-project-vars.txt

# Review file, copy values you need
cat old-project-vars.txt
```

### Tip 3: Set Multiple Variables at Once
```bash
railway variables set \
  TWILIO_ACCOUNT_SID="ACxxxxx" \
  TWILIO_AUTH_TOKEN="token" \
  TWILIO_VERIFY_SERVICE_SID="VAxxxxx" \
  ADMIN_EMAILS="your@email.com"
```

### Tip 4: Verify After Setting
```bash
# List all variables
railway variables

# Check specific variable
railway variables get TWILIO_ACCOUNT_SID
```

---

## ⚠️ **Important Security Note**

### Never Copy These Between Apps:

**❌ FLASK_SECRET_KEY**
- Each app MUST have unique secret
- Security requirement
- Generate fresh for new app

**Why it matters:**
```
If you reuse the secret key:
1. Someone gets secret from App A
2. Can forge sessions for App B
3. Both apps are compromised

If you use different secrets:
1. Someone gets secret from App A
2. Cannot affect App B
3. Only App A is compromised
```

---

## 📊 **Time Comparison**

| Method | Time | Pros | Cons |
|--------|------|------|------|
| **Automated Script** | 2-3 min | Fast, no typing errors | Requires script execution |
| **Manual Copy** | 8-10 min | Full control, understand each step | Tedious, typo risk |
| **Retype Everything** | 15-20 min | Learn all variables | Slow, error-prone |

**Recommendation:** Use automated script

---

## 🎯 **Step-by-Step: Using Automated Script**

### 1. Run the Script
```bash
cd /Users/kcorless/Documents/Projects/OlympicPool2
./copy-railway-config.sh
```

### 2. Select Old Project
- Script prompts you to link to old Railway project
- Select your existing Olympic Medal Pool project
- Script fetches all variables

### 3. Review What Was Found
- Script displays all variables found in old project
- Shows which will be copied
- Shows which will be newly generated

### 4. Generate New Secret
- Script automatically generates new FLASK_SECRET_KEY
- Unique for security

### 5. Select/Create New Project
- Choose to create new project or link to existing
- Script switches context to new project

### 6. Confirm and Set
- Script shows summary of what will be set
- Confirm to proceed
- All variables set automatically

### 7. Verify
- Script displays all variables in new project
- Save summary file for your records

### 8. Done!
- Configuration copied ✅
- New secret generated ✅
- Ready to deploy ✅

---

## 📝 **What Gets Set (Summary)**

### Copied from Old App ✅
```bash
TWILIO_ACCOUNT_SID=<same-as-old>
TWILIO_AUTH_TOKEN=<same-as-old>
TWILIO_VERIFY_SERVICE_SID=<same-as-old>
RESEND_API_KEY=<same-as-old>  # if found
ADMIN_EMAILS=<same-as-old>
GLOBAL_ADMIN_EMAILS=<same-as-old>
NO_SMS_MODE=<same-as-old>
NO_EMAIL_MODE=<same-as-old>
```

### Newly Generated 🔐
```bash
FLASK_SECRET_KEY=<newly-generated-unique-secret>
```

### Production Defaults ⚙️
```bash
FLASK_DEBUG=False
SESSION_COOKIE_SECURE=True
```

### Set After Deployment ⏸️
```bash
BASE_URL=<will-set-after-getting-railway-url>
```

---

## 🚀 **Next Steps After Copying Config**

### 1. Create Volume
```bash
railway volume add --mount-path /app/instance
```

### 2. Deploy App
```bash
railway up
```

### 3. Get Railway URL
```bash
railway domain
```

### 4. Set BASE_URL
```bash
railway variables set BASE_URL="https://your-project.up.railway.app"
```

### 5. Verify Deployment
```bash
./verify-deployment.sh
```

---

## ❓ **FAQ**

**Q: Can I use the same Twilio credentials for both apps?**
A: ✅ Yes! Completely safe. Both apps can share the same Twilio account.

**Q: Do I need to generate a new secret key?**
A: ✅ Yes! Each app MUST have its own unique FLASK_SECRET_KEY for security.

**Q: Can I copy the BASE_URL?**
A: ❌ No. Each app has its own Railway URL. Set after deployment.

**Q: Will copying variables affect my old app?**
A: ❌ No! Variables are per-project. Copying to new project doesn't change old project.

**Q: Can I copy ADMIN_EMAILS?**
A: ✅ Yes! You're the admin of both apps, use the same email addresses.

**Q: What if I make a typo when copying manually?**
A: Use the automated script to avoid typos, or verify with `railway variables` after setting.

**Q: Can I change variables later?**
A: ✅ Yes! Use `railway variables set KEY=value` anytime.

---

## 🎉 **Summary**

### ✅ You CAN Copy (8 variables):
1. TWILIO_ACCOUNT_SID
2. TWILIO_AUTH_TOKEN
3. TWILIO_VERIFY_SERVICE_SID
4. RESEND_API_KEY (optional)
5. ADMIN_EMAILS
6. GLOBAL_ADMIN_EMAILS
7. NO_SMS_MODE
8. NO_EMAIL_MODE

### ❌ You MUST Generate New (1 variable):
1. FLASK_SECRET_KEY (unique for security)

### ⏸️ You Set After Deployment (1 variable):
1. BASE_URL (different URL for each app)

### 🤖 Recommended Method:
```bash
./copy-railway-config.sh
```

**Saves 10-15 minutes and eliminates typing errors!**

---

**Ready to copy your configuration?** Run:
```bash
./copy-railway-config.sh
```
