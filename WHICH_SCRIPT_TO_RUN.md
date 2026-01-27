# Which Script Should I Run?

**You have TWO deployment scripts. Here's when to use each one:**

---

## 🎯 **Quick Answer**

### For FULL deployment (recommended for first-time):
```bash
./deploy-to-railway.sh
```
**Does everything:** Config copy, project creation, volume setup, deployment

### For ONLY copying configuration:
```bash
./copy-railway-config.sh
```
**Does only:** Copies variables from old app to new app

---

## 📋 **Script Comparison**

| Feature | deploy-to-railway.sh | copy-railway-config.sh |
|---------|---------------------|----------------------|
| **Purpose** | Complete deployment | Configuration copy only |
| **What it does** | Everything | Just copies environment variables |
| **When to use** | First deployment | Before manual deployment |
| **Includes config copy?** | Yes | Yes (that's all it does) |
| **Creates Railway project?** | Yes | Yes (optional) |
| **Creates volume?** | Yes | No |
| **Deploys app?** | Yes | No |
| **Time required** | 15-30 min | 2-3 min |

---

## 🚀 **Option 1: Full Deployment (Recommended)**

**Run ONE script that does everything:**

```bash
cd /Users/kcorless/Documents/Projects/OlympicPool2
./deploy-to-railway.sh
```

**This script guides you through:**
1. ✅ Prerequisites check
2. ✅ Railway login
3. ✅ Create new Railway project
4. ✅ Create database volume
5. ✅ **Copy configuration from old app** ← Includes config copy!
6. ✅ Generate new secret key
7. ✅ Set all environment variables
8. ✅ Deploy application
9. ✅ Monitor deployment logs
10. ✅ Set up custom domain (optional)

**Advantage:** One script, handles everything, no steps missed

**Disadvantage:** Takes longer (but only because it does everything)

---

## 🔧 **Option 2: Manual Deployment (Advanced)**

**Run config copy script, then do rest manually:**

### Step 1: Copy Configuration (2-3 minutes)
```bash
cd /Users/kcorless/Documents/Projects/OlympicPool2
./copy-railway-config.sh
```

**This copies environment variables only.**

### Step 2: Create Volume (30 seconds)
```bash
railway volume add --mount-path /app/instance
```

### Step 3: Deploy (2-5 minutes)
```bash
railway up
```

### Step 4: Set BASE_URL (30 seconds)
```bash
railway domain  # Get your URL
railway variables set BASE_URL="https://your-url.railway.app"
```

### Step 5: Verify (2-3 minutes)
```bash
./verify-deployment.sh
```

**Advantage:** Full control over each step

**Disadvantage:** More manual steps, easier to miss something

---

## 🎬 **What Each Script Does in Detail**

### deploy-to-railway.sh (Full Deployment)

```
┌─────────────────────────────────────────┐
│  deploy-to-railway.sh                   │
├─────────────────────────────────────────┤
│                                         │
│  1. Check prerequisites                 │
│     ├─ Railway CLI installed?           │
│     ├─ In correct directory?            │
│     └─ Required files exist?            │
│                                         │
│  2. Railway login                       │
│     └─ Verify authenticated             │
│                                         │
│  3. Initialize Railway project          │
│     ├─ Create new project               │
│     └─ Link to project                  │
│                                         │
│  4. Create database volume              │
│     ├─ Name: database                   │
│     └─ Mount: /app/instance             │
│                                         │
│  5. Copy configuration ←────────────────┼─ Config copy happens HERE
│     ├─ Link to old project              │
│     ├─ Fetch old variables              │
│     ├─ Generate new secret key          │
│     ├─ Link to new project              │
│     └─ Set all variables                │
│                                         │
│  6. Deploy application                  │
│     ├─ railway up                       │
│     └─ Monitor logs                     │
│                                         │
│  7. Get Railway URL                     │
│     └─ Display URL                      │
│                                         │
│  8. Custom domain (optional)            │
│     ├─ Add domain to Railway            │
│     ├─ Show DNS instructions            │
│     └─ Update BASE_URL                  │
│                                         │
│  ✅ Deployment complete                 │
└─────────────────────────────────────────┘
```

### copy-railway-config.sh (Config Only)

```
┌─────────────────────────────────────────┐
│  copy-railway-config.sh                 │
├─────────────────────────────────────────┤
│                                         │
│  1. Link to old project                 │
│     └─ User selects old Railway project │
│                                         │
│  2. Fetch variables from old            │
│     ├─ TWILIO_ACCOUNT_SID              │
│     ├─ TWILIO_AUTH_TOKEN               │
│     ├─ TWILIO_VERIFY_SERVICE_SID       │
│     ├─ RESEND_API_KEY                  │
│     ├─ ADMIN_EMAILS                    │
│     └─ Other config flags              │
│                                         │
│  3. Generate new secret key             │
│     └─ FLASK_SECRET_KEY (unique)        │
│                                         │
│  4. Link to new project                 │
│     ├─ Create new OR                    │
│     └─ Link to existing                 │
│                                         │
│  5. Set variables in new project        │
│     ├─ Copy from old (8 variables)      │
│     ├─ New secret key (1 variable)      │
│     └─ Production defaults              │
│                                         │
│  ✅ Configuration copied                │
│                                         │
│  ⏭️  Next: You manually do:             │
│     - Create volume                     │
│     - Deploy app                        │
│     - Set BASE_URL                      │
└─────────────────────────────────────────┘
```

---

## 🤔 **Which Should You Use?**

### Use **deploy-to-railway.sh** if:
- ✅ First time deploying
- ✅ Want guided step-by-step process
- ✅ Want one script to do everything
- ✅ Don't want to miss any steps
- ✅ Prefer interactive prompts

**→ This is RECOMMENDED for most users**

### Use **copy-railway-config.sh** if:
- You want to copy config first, then do other steps later
- You prefer manual control over each deployment step
- You're familiar with Railway CLI
- You want to review each step carefully before executing

---

## 📝 **Recommended Workflow (First-Time Deployment)**

### Simple: Just Run Full Deployment Script
```bash
cd /Users/kcorless/Documents/Projects/OlympicPool2
./deploy-to-railway.sh
```

**That's it!** The script handles everything including copying your configuration from the old app.

---

## ⚙️ **Advanced Workflow (Manual Control)**

If you prefer manual control:

```bash
# Step 1: Copy configuration
cd /Users/kcorless/Documents/Projects/OlympicPool2
./copy-railway-config.sh
# ✅ Variables copied

# Step 2: Create volume
railway volume add --mount-path /app/instance
# ✅ Volume created

# Step 3: Deploy
railway up
# ✅ App deployed

# Step 4: Get URL and set BASE_URL
RAILWAY_URL=$(railway domain | grep -o 'https://[^ ]*' | head -1)
railway variables set BASE_URL="$RAILWAY_URL"
# ✅ BASE_URL set

# Step 5: Verify
./verify-deployment.sh
# ✅ Deployment verified
```

---

## 🎯 **Answer to Your Specific Question**

> "So just run ./copy-railway-config.sh from my local olympicpool2 directory?"

**Answer:** You CAN, but it only copies configuration. You'd still need to:
1. Create volume manually
2. Deploy manually
3. Set BASE_URL manually

**Better answer:** Run `./deploy-to-railway.sh` instead - it does EVERYTHING including the config copy!

> "Is this one script that does all the deployment?"

- `deploy-to-railway.sh` = **YES**, does full deployment
- `copy-railway-config.sh` = **NO**, only copies config

> "Or is it a copy script that I run at a specific point of the script?"

- `copy-railway-config.sh` = Standalone script for config copy only
- You DON'T need to run it if you use `deploy-to-railway.sh` (which includes config copy)

---

## 🚦 **Decision Tree**

```
Start Here
    ↓
Do you want ONE script to do everything?
    ↓
    ├─ YES → Run: ./deploy-to-railway.sh
    │         └─ Done! ✅
    │
    └─ NO → Want manual control?
            ↓
            ├─ Step 1: ./copy-railway-config.sh
            ├─ Step 2: railway volume add --mount-path /app/instance
            ├─ Step 3: railway up
            ├─ Step 4: railway variables set BASE_URL="..."
            └─ Step 5: ./verify-deployment.sh
```

---

## 📊 **Script Contents Summary**

### deploy-to-railway.sh includes:
- ✅ Prerequisites check
- ✅ Railway project creation
- ✅ Volume creation
- ✅ **Configuration copy (from old app)**
- ✅ Environment variable setup
- ✅ Application deployment
- ✅ Deployment monitoring
- ✅ Custom domain setup

### copy-railway-config.sh includes:
- ✅ **Configuration copy only (from old app)**
- ❌ Everything else you do manually

---

## 💡 **Recommendation**

**For first-time deployment, use the FULL script:**

```bash
cd /Users/kcorless/Documents/Projects/OlympicPool2
./deploy-to-railway.sh
```

**Why:**
- Handles everything in one go
- Interactive prompts guide you
- Can't miss steps
- Includes config copy automatically
- Takes 15-30 minutes total
- Most reliable for first deployment

**Save the manual method for later deployments when you know the process.**

---

## ✅ **TL;DR**

| Your Question | Answer |
|--------------|---------|
| Which script to run? | `./deploy-to-railway.sh` (recommended) |
| Does it do full deployment? | YES |
| Does it copy config? | YES (automatically) |
| Do I need to run copy script separately? | NO (already included) |
| Just run from olympicpool2 directory? | YES |

**One command:**
```bash
./deploy-to-railway.sh
```

**That's it!** 🎉
