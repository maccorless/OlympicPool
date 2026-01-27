#!/bin/bash
# Railway Deployment Helper Script
# This script provides step-by-step deployment instructions and generates commands

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_step() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_command() {
    echo -e "${YELLOW}$ $1${NC}"
}

# Check if Railway CLI is installed
check_railway_cli() {
    if ! command -v railway &> /dev/null; then
        print_error "Railway CLI not found!"
        echo ""
        echo "Install Railway CLI with:"
        print_command "npm install -g @railway/cli"
        echo ""
        exit 1
    fi
    print_step "Railway CLI is installed"
}

# Main script
clear
echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║       Railway Deployment Helper - OlympicPool2          ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

print_header "Step 1: Prerequisites Check"

# Check Railway CLI
check_railway_cli

# Check if in project directory
if [ ! -f "app/__init__.py" ]; then
    print_error "Not in project directory!"
    echo "Please run this script from the OlympicPool2 project root."
    exit 1
fi
print_step "In correct project directory"

# Check for Dockerfile
if [ ! -f "Dockerfile" ]; then
    print_error "Dockerfile not found!"
    exit 1
fi
print_step "Dockerfile found"

# Check for railway.toml
if [ ! -f "railway.toml" ]; then
    print_error "railway.toml not found!"
    exit 1
fi
print_step "railway.toml found"

# Check for start.sh
if [ ! -f "start.sh" ]; then
    print_error "start.sh not found!"
    exit 1
fi
print_step "start.sh found"

print_header "Step 2: Railway Login"
echo "Make sure you're logged into Railway:"
print_command "railway login"
echo ""
read -p "Press Enter when logged in..."

print_header "Step 3: Initialize Railway Project"
echo "This will create a new Railway project."
echo ""
print_warning "If you already have a project, skip this step."
echo ""
read -p "Create new Railway project? (y/N): " create_project

if [[ $create_project =~ ^[Yy]$ ]]; then
    print_command "railway init"
    railway init
    print_step "Railway project created"
else
    print_step "Skipping project creation"
fi

print_header "Step 4: Create Database Volume"
echo "Database volume is REQUIRED for data persistence."
echo ""
print_warning "This must be created before first deployment!"
echo ""
read -p "Create database volume? (y/N): " create_volume

if [[ $create_volume =~ ^[Yy]$ ]]; then
    print_command "railway volume add --mount-path /app/instance"
    railway volume add --mount-path /app/instance
    print_step "Database volume created"

    echo ""
    echo "Verifying volume..."
    railway volume list
else
    print_step "Skipping volume creation"
fi

print_header "Step 5: Generate Secret Key"
echo "Generating a strong Flask secret key..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
print_step "Secret key generated: $SECRET_KEY"
echo ""
print_warning "Save this key! You'll need it in the next step."
echo ""

print_header "Step 6: Set Environment Variables"
echo "You need to configure environment variables before deployment."
echo ""
echo "Choose a method:"
echo "  1) Set via Railway CLI (recommended)"
echo "  2) Set via Railway Dashboard (manual)"
echo ""
read -p "Choose (1/2): " var_method

if [ "$var_method" = "1" ]; then
    echo ""
    echo "Please provide the following information:"
    echo ""

    # Admin email
    read -p "Admin email address: " admin_email

    # Twilio credentials
    echo ""
    print_warning "Twilio credentials (for SMS OTP)"
    read -p "Twilio Account SID (or press Enter to skip): " twilio_sid
    read -p "Twilio Auth Token (or press Enter to skip): " twilio_token
    read -p "Twilio Verify Service SID (or press Enter to skip): " twilio_service

    # Resend API key (optional)
    echo ""
    print_warning "Resend API key (optional - for email)"
    read -p "Resend API Key (or press Enter to skip): " resend_key

    echo ""
    echo "Setting environment variables..."
    echo ""

    # Core configuration
    print_command "railway variables set FLASK_SECRET_KEY=\"$SECRET_KEY\""
    railway variables set FLASK_SECRET_KEY="$SECRET_KEY"

    print_command "railway variables set FLASK_DEBUG=False"
    railway variables set FLASK_DEBUG=False

    print_command "railway variables set SESSION_COOKIE_SECURE=True"
    railway variables set SESSION_COOKIE_SECURE=True

    # Admin emails
    print_command "railway variables set ADMIN_EMAILS=\"$admin_email\""
    railway variables set ADMIN_EMAILS="$admin_email"

    print_command "railway variables set GLOBAL_ADMIN_EMAILS=\"$admin_email\""
    railway variables set GLOBAL_ADMIN_EMAILS="$admin_email"

    # Twilio (if provided)
    if [ ! -z "$twilio_sid" ]; then
        print_command "railway variables set TWILIO_ACCOUNT_SID=\"$twilio_sid\""
        railway variables set TWILIO_ACCOUNT_SID="$twilio_sid"

        print_command "railway variables set TWILIO_AUTH_TOKEN=\"$twilio_token\""
        railway variables set TWILIO_AUTH_TOKEN="$twilio_token"

        print_command "railway variables set TWILIO_VERIFY_SERVICE_SID=\"$twilio_service\""
        railway variables set TWILIO_VERIFY_SERVICE_SID="$twilio_service"

        print_command "railway variables set NO_SMS_MODE=False"
        railway variables set NO_SMS_MODE=False
    else
        print_warning "No Twilio credentials - setting NO_SMS_MODE=True"
        print_command "railway variables set NO_SMS_MODE=True"
        railway variables set NO_SMS_MODE=True
    fi

    # Resend (if provided)
    if [ ! -z "$resend_key" ]; then
        print_command "railway variables set RESEND_API_KEY=\"$resend_key\""
        railway variables set RESEND_API_KEY="$resend_key"

        print_command "railway variables set NO_EMAIL_MODE=False"
        railway variables set NO_EMAIL_MODE=False
    else
        print_command "railway variables set NO_EMAIL_MODE=True"
        railway variables set NO_EMAIL_MODE=True
    fi

    # Get Railway domain and set BASE_URL
    echo ""
    echo "Getting Railway domain..."
    RAILWAY_DOMAIN=$(railway domain 2>/dev/null | grep -o 'https://[^ ]*' | head -1 || echo "")

    if [ ! -z "$RAILWAY_DOMAIN" ]; then
        print_command "railway variables set BASE_URL=\"$RAILWAY_DOMAIN\""
        railway variables set BASE_URL="$RAILWAY_DOMAIN"
        print_step "BASE_URL set to: $RAILWAY_DOMAIN"
    else
        print_warning "Could not get Railway domain. You'll need to set BASE_URL manually after deployment."
    fi

    echo ""
    print_step "Environment variables configured!"

    echo ""
    echo "Verify variables:"
    railway variables

elif [ "$var_method" = "2" ]; then
    echo ""
    print_warning "Manual configuration required"
    echo ""
    echo "Go to Railway Dashboard:"
    echo "1. Open https://railway.app/dashboard"
    echo "2. Select your project"
    echo "3. Click 'Variables' tab"
    echo "4. Add these variables:"
    echo ""
    echo "   FLASK_SECRET_KEY = $SECRET_KEY"
    echo "   FLASK_DEBUG = False"
    echo "   SESSION_COOKIE_SECURE = True"
    echo "   ADMIN_EMAILS = your@email.com"
    echo "   GLOBAL_ADMIN_EMAILS = your@email.com"
    echo "   TWILIO_ACCOUNT_SID = ACxxxxx"
    echo "   TWILIO_AUTH_TOKEN = xxxxx"
    echo "   TWILIO_VERIFY_SERVICE_SID = VAxxxxx"
    echo "   NO_SMS_MODE = False (or True for testing)"
    echo "   RESEND_API_KEY = re_xxxxx (optional)"
    echo "   NO_EMAIL_MODE = True"
    echo "   BASE_URL = (will be set after getting Railway URL)"
    echo ""
    read -p "Press Enter when variables are configured..."
else
    print_error "Invalid choice"
    exit 1
fi

print_header "Step 7: Deploy Application"
echo "Ready to deploy!"
echo ""
echo "You can deploy in two ways:"
echo "  1) Automatic (via GitHub push) - Recommended"
echo "  2) Manual (via railway up)"
echo ""
read -p "Choose deployment method (1/2): " deploy_method

if [ "$deploy_method" = "1" ]; then
    echo ""
    print_warning "Automatic deployment via GitHub"
    echo ""
    echo "Push your changes to trigger deployment:"
    print_command "git add ."
    print_command "git commit -m \"Configure for Railway deployment\""
    print_command "git push origin main"
    echo ""
    echo "Railway will automatically build and deploy."
    echo ""
    read -p "Press Enter when deployment is complete..."

elif [ "$deploy_method" = "2" ]; then
    echo ""
    print_command "railway up"
    railway up
    print_step "Deployment initiated"
else
    print_error "Invalid choice"
    exit 1
fi

print_header "Step 8: Monitor Deployment"
echo "Watch deployment logs:"
print_command "railway logs --follow"
echo ""
read -p "View logs now? (y/N): " view_logs

if [[ $view_logs =~ ^[Yy]$ ]]; then
    railway logs --follow
fi

print_header "Step 9: Get Railway URL"
echo "Your application URL:"
railway domain
echo ""

print_header "Step 10: Custom Domain (Optional)"
echo "To use medalpool.com:"
echo ""
echo "1. Add custom domain:"
print_command "railway domain add medalpool.com"
echo ""
echo "2. Configure DNS at your registrar:"
echo "   - Add CNAME record: @ → <your-project>.up.railway.app"
echo "   - Wait for DNS propagation (5-60 minutes)"
echo ""
echo "3. Update BASE_URL:"
print_command "railway variables set BASE_URL=\"https://medalpool.com\""
echo ""
read -p "Set up custom domain now? (y/N): " setup_domain

if [[ $setup_domain =~ ^[Yy]$ ]]; then
    read -p "Enter your custom domain: " custom_domain
    print_command "railway domain add $custom_domain"
    railway domain add $custom_domain

    echo ""
    print_step "Custom domain added!"
    echo ""
    print_warning "Configure DNS at your registrar, then update BASE_URL:"
    echo ""
    print_command "railway variables set BASE_URL=\"https://$custom_domain\""
fi

print_header "Deployment Complete! 🚀"
echo "Next steps:"
echo ""
echo "1. Test your application at the Railway URL"
echo "2. Access Global Admin: https://your-url/admin/global"
echo "3. Create your first event and contest"
echo "4. Set contest state to 'open' when ready"
echo "5. Share the contest URL with users"
echo ""
echo "Useful commands:"
echo "  railway logs          - View logs"
echo "  railway status        - Check status"
echo "  railway domain        - View domains"
echo "  railway variables     - List variables"
echo "  railway open          - Open in browser"
echo ""
echo "For detailed documentation, see DEPLOYMENT.md"
echo ""
print_step "All done!"
