#!/bin/bash
# Copy Railway Configuration Variables from Old App to New App
# This script helps you copy reusable variables and generates new ones where needed

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

clear
echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║     Copy Railway Configuration - Old → New App          ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

print_header "Step 1: Get Variables from Old App"

echo "First, we need to link to your OLD Railway project."
echo ""
read -p "Press Enter to select your OLD project..."

# Link to old project
railway link

echo ""
print_info "Fetching variables from old project..."
echo ""

# Get variables from old project
TWILIO_SID=$(railway variables get TWILIO_ACCOUNT_SID 2>/dev/null || echo "")
TWILIO_TOKEN=$(railway variables get TWILIO_AUTH_TOKEN 2>/dev/null || echo "")
TWILIO_SERVICE=$(railway variables get TWILIO_VERIFY_SERVICE_SID 2>/dev/null || echo "")
RESEND_KEY=$(railway variables get RESEND_API_KEY 2>/dev/null || echo "")
ADMIN_EMAILS=$(railway variables get ADMIN_EMAILS 2>/dev/null || echo "")
GLOBAL_ADMIN_EMAILS=$(railway variables get GLOBAL_ADMIN_EMAILS 2>/dev/null || echo "")
NO_SMS=$(railway variables get NO_SMS_MODE 2>/dev/null || echo "")
NO_EMAIL=$(railway variables get NO_EMAIL_MODE 2>/dev/null || echo "")

# Display what was found
echo ""
print_header "Variables Found in Old App"
echo ""

if [ ! -z "$TWILIO_SID" ]; then
    print_success "TWILIO_ACCOUNT_SID: ${TWILIO_SID:0:10}... (will copy)"
else
    print_warning "TWILIO_ACCOUNT_SID: Not found"
fi

if [ ! -z "$TWILIO_TOKEN" ]; then
    print_success "TWILIO_AUTH_TOKEN: ******* (will copy)"
else
    print_warning "TWILIO_AUTH_TOKEN: Not found"
fi

if [ ! -z "$TWILIO_SERVICE" ]; then
    print_success "TWILIO_VERIFY_SERVICE_SID: ${TWILIO_SERVICE:0:10}... (will copy)"
else
    print_warning "TWILIO_VERIFY_SERVICE_SID: Not found"
fi

if [ ! -z "$RESEND_KEY" ]; then
    print_success "RESEND_API_KEY: ${RESEND_KEY:0:10}... (will copy)"
else
    print_info "RESEND_API_KEY: Not found (optional)"
fi

if [ ! -z "$ADMIN_EMAILS" ]; then
    print_success "ADMIN_EMAILS: $ADMIN_EMAILS (will copy)"
else
    print_warning "ADMIN_EMAILS: Not found"
fi

if [ ! -z "$GLOBAL_ADMIN_EMAILS" ]; then
    print_success "GLOBAL_ADMIN_EMAILS: $GLOBAL_ADMIN_EMAILS (will copy)"
else
    print_info "GLOBAL_ADMIN_EMAILS: Not found (will use ADMIN_EMAILS)"
fi

if [ ! -z "$NO_SMS" ]; then
    print_success "NO_SMS_MODE: $NO_SMS (will copy)"
else
    print_info "NO_SMS_MODE: Not set (will default to False)"
fi

if [ ! -z "$NO_EMAIL" ]; then
    print_success "NO_EMAIL_MODE: $NO_EMAIL (will copy)"
else
    print_info "NO_EMAIL_MODE: Not set (will default to True)"
fi

print_header "Step 2: Generate New Variables"

echo "Some variables MUST be unique for security:"
echo ""

# Generate new secret key
print_info "Generating NEW Flask secret key (MUST be unique per app)..."
NEW_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
print_success "FLASK_SECRET_KEY: Generated (${NEW_SECRET:0:16}...)"

echo ""
print_warning "❌ Do NOT reuse FLASK_SECRET_KEY from old app!"
print_warning "Each app must have its own unique secret for security."

print_header "Step 3: Switch to New App"

echo "Now we'll link to your NEW Railway project."
echo ""
echo "Options:"
echo "  1. Create a new project now (if you haven't already)"
echo "  2. Link to existing new project"
echo ""
read -p "Choose (1/2): " choice

if [ "$choice" = "1" ]; then
    echo ""
    print_info "Creating new Railway project..."
    echo ""

    cd /Users/kcorless/Documents/Projects/OlympicPool2
    railway init

    print_success "New project created!"
elif [ "$choice" = "2" ]; then
    echo ""
    print_info "Linking to existing project..."
    echo ""

    cd /Users/kcorless/Documents/Projects/OlympicPool2
    railway link

    print_success "Linked to project!"
else
    print_error "Invalid choice"
    exit 1
fi

print_header "Step 4: Set Variables in New App"

echo "Now we'll set all the variables in your new app."
echo ""
echo "Variables to be set:"
echo ""
echo "✅ COPIED from old app:"
echo "   - TWILIO_ACCOUNT_SID"
echo "   - TWILIO_AUTH_TOKEN"
echo "   - TWILIO_VERIFY_SERVICE_SID"
echo "   - RESEND_API_KEY (if found)"
echo "   - ADMIN_EMAILS"
echo "   - GLOBAL_ADMIN_EMAILS"
echo "   - NO_SMS_MODE"
echo "   - NO_EMAIL_MODE"
echo ""
echo "🔐 NEWLY GENERATED:"
echo "   - FLASK_SECRET_KEY (unique for security)"
echo ""
echo "⚙️  PRODUCTION DEFAULTS:"
echo "   - FLASK_DEBUG=False"
echo "   - SESSION_COOKIE_SECURE=True"
echo ""
echo "⏸️  WILL SET LATER:"
echo "   - BASE_URL (after getting Railway URL)"
echo ""
read -p "Ready to set variables? (y/N): " confirm

if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo ""
    print_warning "Variables not set. You can set them manually later."
    exit 0
fi

echo ""
print_info "Setting variables..."
echo ""

# Set copied variables
if [ ! -z "$TWILIO_SID" ]; then
    railway variables --set TWILIO_ACCOUNT_SID="$TWILIO_SID"
    print_success "Set TWILIO_ACCOUNT_SID"
fi

if [ ! -z "$TWILIO_TOKEN" ]; then
    railway variables --set TWILIO_AUTH_TOKEN="$TWILIO_TOKEN"
    print_success "Set TWILIO_AUTH_TOKEN"
fi

if [ ! -z "$TWILIO_SERVICE" ]; then
    railway variables --set TWILIO_VERIFY_SERVICE_SID="$TWILIO_SERVICE"
    print_success "Set TWILIO_VERIFY_SERVICE_SID"
fi

if [ ! -z "$RESEND_KEY" ]; then
    railway variables --set RESEND_API_KEY="$RESEND_KEY"
    print_success "Set RESEND_API_KEY"
fi

if [ ! -z "$ADMIN_EMAILS" ]; then
    railway variables --set ADMIN_EMAILS="$ADMIN_EMAILS"
    print_success "Set ADMIN_EMAILS"
fi

if [ ! -z "$GLOBAL_ADMIN_EMAILS" ]; then
    railway variables --set GLOBAL_ADMIN_EMAILS="$GLOBAL_ADMIN_EMAILS"
    print_success "Set GLOBAL_ADMIN_EMAILS"
elif [ ! -z "$ADMIN_EMAILS" ]; then
    railway variables --set GLOBAL_ADMIN_EMAILS="$ADMIN_EMAILS"
    print_success "Set GLOBAL_ADMIN_EMAILS (from ADMIN_EMAILS)"
fi

# Set new secret key
railway variables --set FLASK_SECRET_KEY="$NEW_SECRET"
print_success "Set FLASK_SECRET_KEY (NEW unique key)"

# Set production defaults
railway variables --set FLASK_DEBUG=False
print_success "Set FLASK_DEBUG=False"

railway variables --set SESSION_COOKIE_SECURE=True
print_success "Set SESSION_COOKIE_SECURE=True"

# Set SMS/Email modes
if [ ! -z "$NO_SMS" ]; then
    railway variables --set NO_SMS_MODE="$NO_SMS"
    print_success "Set NO_SMS_MODE=$NO_SMS"
else
    railway variables --set NO_SMS_MODE=False
    print_success "Set NO_SMS_MODE=False (default for production)"
fi

if [ ! -z "$NO_EMAIL" ]; then
    railway variables --set NO_EMAIL_MODE="$NO_EMAIL"
    print_success "Set NO_EMAIL_MODE=$NO_EMAIL"
else
    railway variables --set NO_EMAIL_MODE=True
    print_success "Set NO_EMAIL_MODE=True (default)"
fi

print_header "Step 5: Verification"

echo "Let's verify all variables were set correctly:"
echo ""

railway variables

print_header "Summary"

echo -e "${GREEN}✓ Configuration copied successfully!${NC}"
echo ""
echo "Variables copied from old app:"
echo "  ✅ Twilio credentials (safe to share)"
echo "  ✅ Resend API key (if found)"
echo "  ✅ Admin emails"
echo "  ✅ SMS/Email modes"
echo ""
echo "New variables generated:"
echo "  🔐 FLASK_SECRET_KEY (unique for security)"
echo ""
echo "Production settings applied:"
echo "  ⚙️  FLASK_DEBUG=False"
echo "  ⚙️  SESSION_COOKIE_SECURE=True"
echo ""
echo "Still need to set:"
echo "  ⏸️  BASE_URL (set after deployment)"
echo ""
echo "Next steps:"
echo "  1. Create volume: railway volume add --mount-path /app/instance"
echo "  2. Deploy app: railway up"
echo "  3. Get Railway URL: railway domain"
echo "  4. Set BASE_URL: railway variables --set BASE_URL=\"<your-railway-url>\""
echo ""
echo "Or run the full deployment script:"
echo "  ./deploy-to-railway.sh"
echo ""

# Save summary to file
SUMMARY_FILE="config-copy-summary-$(date +%Y%m%d-%H%M%S).txt"
{
    echo "Configuration Copy Summary"
    echo "========================="
    echo "Date: $(date)"
    echo ""
    echo "Variables copied from old app:"
    echo "  - TWILIO_ACCOUNT_SID: ${TWILIO_SID:0:20}..."
    echo "  - TWILIO_AUTH_TOKEN: *******"
    echo "  - TWILIO_VERIFY_SERVICE_SID: ${TWILIO_SERVICE:0:20}..."
    [ ! -z "$RESEND_KEY" ] && echo "  - RESEND_API_KEY: ${RESEND_KEY:0:20}..."
    echo "  - ADMIN_EMAILS: $ADMIN_EMAILS"
    [ ! -z "$GLOBAL_ADMIN_EMAILS" ] && echo "  - GLOBAL_ADMIN_EMAILS: $GLOBAL_ADMIN_EMAILS"
    echo ""
    echo "New variables generated:"
    echo "  - FLASK_SECRET_KEY: ${NEW_SECRET:0:20}... (unique)"
    echo ""
    echo "Production settings:"
    echo "  - FLASK_DEBUG: False"
    echo "  - SESSION_COOKIE_SECURE: True"
    echo "  - NO_SMS_MODE: ${NO_SMS:-False}"
    echo "  - NO_EMAIL_MODE: ${NO_EMAIL:-True}"
} > "$SUMMARY_FILE"

echo "Summary saved to: $SUMMARY_FILE"
echo ""
print_success "Done! 🎉"
