#!/bin/bash
# Post-Deployment Verification Script
# Verifies Railway deployment is working correctly

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_test() {
    echo -e "${BLUE}Testing:${NC} $1"
}

print_pass() {
    echo -e "${GREEN}✓ PASS${NC} $1"
    ((PASSED++))
}

print_fail() {
    echo -e "${RED}✗ FAIL${NC} $1"
    ((FAILED++))
}

print_warn() {
    echo -e "${YELLOW}⚠ WARN${NC} $1"
    ((WARNINGS++))
}

print_info() {
    echo -e "${BLUE}ℹ INFO${NC} $1"
}

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${RED}Error: Railway CLI not found${NC}"
    echo "Install with: npm install -g @railway/cli"
    exit 1
fi

clear
echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║      Post-Deployment Verification - OlympicPool2        ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Get deployment URL
print_header "Step 1: Get Deployment URL"
RAILWAY_URL=$(railway domain 2>/dev/null | grep -o 'https://[^ ]*' | head -1 || echo "")

if [ -z "$RAILWAY_URL" ]; then
    echo -e "${RED}Could not get Railway URL${NC}"
    read -p "Enter your Railway URL: " RAILWAY_URL
fi

echo "Testing URL: $RAILWAY_URL"
BASE_URL="${RAILWAY_URL%/}"  # Remove trailing slash

# Test 1: Basic Connectivity
print_header "Step 2: Basic Connectivity Tests"

print_test "Homepage responds"
if curl -f -s -o /dev/null -w "%{http_code}" "$BASE_URL/" | grep -q "200\|302"; then
    print_pass "Homepage accessible (HTTP 200/302)"
else
    print_fail "Homepage not accessible"
fi

print_test "SSL certificate valid"
if curl -f -s -o /dev/null "$BASE_URL/" 2>&1 | grep -q "SSL certificate problem"; then
    print_fail "SSL certificate invalid"
else
    print_pass "SSL certificate valid"
fi

# Test 2: Railway Service Health
print_header "Step 3: Railway Service Health"

print_test "Railway service status"
if railway status 2>&1 | grep -q "Active\|Running"; then
    print_pass "Service is running"
else
    print_fail "Service not running"
fi

print_test "Recent deployments"
RECENT_DEPLOY=$(railway logs 2>&1 | grep -c "Starting Olympic Medal Pool" || echo "0")
if [ "$RECENT_DEPLOY" -gt 0 ]; then
    print_pass "Found recent deployment logs"
else
    print_warn "No recent deployment logs found"
fi

# Test 3: Environment Variables
print_header "Step 4: Environment Variables Check"

print_test "FLASK_SECRET_KEY set"
if railway run env 2>&1 | grep -q "FLASK_SECRET_KEY"; then
    print_pass "FLASK_SECRET_KEY is set"
else
    print_fail "FLASK_SECRET_KEY not set"
fi

print_test "FLASK_DEBUG disabled"
if railway run env 2>&1 | grep "FLASK_DEBUG" | grep -q -i "false"; then
    print_pass "FLASK_DEBUG=False (correct for production)"
elif railway run env 2>&1 | grep "FLASK_DEBUG" | grep -q -i "true"; then
    print_fail "FLASK_DEBUG=True (should be False in production)"
else
    print_warn "FLASK_DEBUG not explicitly set"
fi

print_test "SESSION_COOKIE_SECURE enabled"
if railway run env 2>&1 | grep "SESSION_COOKIE_SECURE" | grep -q -i "true"; then
    print_pass "SESSION_COOKIE_SECURE=True"
else
    print_fail "SESSION_COOKIE_SECURE not True (required for HTTPS)"
fi

print_test "Admin emails configured"
if railway run env 2>&1 | grep -q "ADMIN_EMAILS"; then
    print_pass "ADMIN_EMAILS is set"
else
    print_fail "ADMIN_EMAILS not set"
fi

print_test "Twilio configured"
if railway run env 2>&1 | grep -q "TWILIO_ACCOUNT_SID"; then
    print_pass "Twilio credentials found"
else
    print_warn "Twilio not configured (SMS won't work)"
fi

# Test 4: Database
print_header "Step 5: Database Verification"

print_test "Database file exists"
if railway run test -f /app/instance/medal_pool.db 2>&1 | grep -q ""; then
    print_pass "Database file exists at /app/instance/medal_pool.db"
else
    print_fail "Database file not found"
fi

print_test "Database has schema"
TABLE_COUNT=$(railway run sqlite3 /app/instance/medal_pool.db "SELECT name FROM sqlite_master WHERE type='table';" 2>&1 | wc -l || echo "0")
if [ "$TABLE_COUNT" -gt 5 ]; then
    print_pass "Database has $TABLE_COUNT tables"
else
    print_fail "Database schema incomplete (only $TABLE_COUNT tables)"
fi

print_test "Countries loaded"
COUNTRY_COUNT=$(railway run sqlite3 /app/instance/medal_pool.db "SELECT COUNT(*) FROM countries;" 2>&1 | tail -1 || echo "0")
if [ "$COUNTRY_COUNT" -gt 0 ]; then
    print_pass "Database has $COUNTRY_COUNT countries"
else
    print_fail "No countries loaded"
fi

print_test "Events table exists"
if railway run sqlite3 /app/instance/medal_pool.db "SELECT name FROM sqlite_master WHERE type='table' AND name='events';" 2>&1 | grep -q "events"; then
    print_pass "Events table exists"
else
    print_fail "Events table missing"
fi

print_test "Contest table exists"
if railway run sqlite3 /app/instance/medal_pool.db "SELECT name FROM sqlite_master WHERE type='table' AND name='contest';" 2>&1 | grep -q "contest"; then
    print_pass "Contest table exists"
else
    print_fail "Contest table missing"
fi

# Test 5: Volume
print_header "Step 6: Volume Persistence Check"

print_test "Volume mounted"
if railway volume list 2>&1 | grep -q "/app/instance"; then
    print_pass "Volume mounted at /app/instance"
else
    print_fail "Volume not mounted (database won't persist!)"
fi

print_test "Volume writable"
if railway run touch /app/instance/test-write 2>&1; then
    print_pass "Volume is writable"
    railway run rm /app/instance/test-write 2>&1
else
    print_fail "Volume is not writable"
fi

# Test 6: Application Routes
print_header "Step 7: Application Routes Test"

print_test "Homepage (/) responds"
if curl -f -s "$BASE_URL/" > /dev/null; then
    print_pass "Homepage accessible"
else
    print_fail "Homepage not accessible"
fi

print_test "Global Admin route exists"
ADMIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/admin/global")
if [ "$ADMIN_STATUS" = "200" ] || [ "$ADMIN_STATUS" = "302" ] || [ "$ADMIN_STATUS" = "401" ]; then
    print_pass "Global admin route exists (HTTP $ADMIN_STATUS)"
else
    print_fail "Global admin route not working (HTTP $ADMIN_STATUS)"
fi

# Test 7: Gunicorn
print_header "Step 8: Gunicorn Process Check"

print_test "Gunicorn running"
if railway run ps aux 2>&1 | grep -q "gunicorn"; then
    print_pass "Gunicorn process found"
else
    print_fail "Gunicorn not running"
fi

print_test "Multiple workers (if expected)"
WORKER_COUNT=$(railway run ps aux 2>&1 | grep -c "gunicorn" || echo "0")
if [ "$WORKER_COUNT" -gt 1 ]; then
    print_pass "Gunicorn has $WORKER_COUNT workers"
else
    print_info "Gunicorn has $WORKER_COUNT worker (single-worker setup)"
fi

# Test 8: Logs
print_header "Step 9: Log Analysis"

print_test "No recent errors in logs"
ERROR_COUNT=$(railway logs 2>&1 | grep -i -c "error\|exception\|traceback" || echo "0")
if [ "$ERROR_COUNT" -eq 0 ]; then
    print_pass "No errors in recent logs"
elif [ "$ERROR_COUNT" -lt 3 ]; then
    print_warn "$ERROR_COUNT errors found in recent logs"
else
    print_fail "$ERROR_COUNT errors found in recent logs"
fi

print_test "App started successfully"
if railway logs 2>&1 | grep -q "Starting gunicorn\|Listening at"; then
    print_pass "App started successfully"
else
    print_warn "Could not confirm successful startup"
fi

# Test 9: Performance
print_header "Step 10: Performance Check"

print_test "Response time"
RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" "$BASE_URL/")
RESPONSE_MS=$(echo "$RESPONSE_TIME * 1000" | bc)
if (( $(echo "$RESPONSE_TIME < 2.0" | bc -l) )); then
    print_pass "Response time: ${RESPONSE_MS}ms (< 2s)"
elif (( $(echo "$RESPONSE_TIME < 5.0" | bc -l) )); then
    print_warn "Response time: ${RESPONSE_MS}ms (slow, 2-5s)"
else
    print_fail "Response time: ${RESPONSE_MS}ms (very slow, > 5s)"
fi

# Test 10: Domain (if custom domain)
print_header "Step 11: Custom Domain Check (Optional)"

read -p "Are you using a custom domain? (y/N): " USING_CUSTOM
if [[ $USING_CUSTOM =~ ^[Yy]$ ]]; then
    read -p "Enter your custom domain (e.g., medalpool.com): " CUSTOM_DOMAIN

    print_test "Custom domain resolves"
    if dig +short "$CUSTOM_DOMAIN" | grep -q "[0-9]"; then
        print_pass "Domain resolves to IP"
    else
        print_fail "Domain does not resolve"
    fi

    print_test "Custom domain accessible"
    if curl -f -s "https://$CUSTOM_DOMAIN" > /dev/null; then
        print_pass "Custom domain accessible"
    else
        print_fail "Custom domain not accessible"
    fi

    print_test "SSL on custom domain"
    if curl -f -s -o /dev/null "https://$CUSTOM_DOMAIN" 2>&1 | grep -q "SSL certificate problem"; then
        print_fail "SSL certificate invalid on custom domain"
    else
        print_pass "SSL certificate valid on custom domain"
    fi
fi

# Summary
print_header "Verification Summary"

TOTAL=$((PASSED + FAILED + WARNINGS))

echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo "Total: $TOTAL"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All critical tests passed!${NC}"
    echo ""
    echo "Your deployment appears to be working correctly."
    echo ""
    echo "Next steps:"
    echo "  1. Access Global Admin: $BASE_URL/admin/global"
    echo "  2. Create your first event and contest"
    echo "  3. Test user registration and login"
    echo "  4. Test draft picker and picks submission"
    echo "  5. Set up regular database backups"
    echo ""
elif [ $FAILED -lt 3 ]; then
    echo -e "${YELLOW}⚠ Some tests failed, but deployment may still work${NC}"
    echo ""
    echo "Review the failed tests above and address them."
    echo "Check logs with: railway logs --follow"
    echo ""
else
    echo -e "${RED}✗ Multiple critical failures detected${NC}"
    echo ""
    echo "Deployment has issues that need to be resolved."
    echo ""
    echo "Troubleshooting steps:"
    echo "  1. Check logs: railway logs --follow"
    echo "  2. Verify environment variables: railway variables"
    echo "  3. Verify volume: railway volume list"
    echo "  4. Check service status: railway status"
    echo "  5. Review DEPLOYMENT.md troubleshooting section"
    echo ""
    echo "If issues persist, consider rollback: railway rollback"
    echo ""
fi

# Save results to file
REPORT_FILE="verification-report-$(date +%Y%m%d-%H%M%S).txt"
{
    echo "Deployment Verification Report"
    echo "=============================="
    echo "Date: $(date)"
    echo "URL: $BASE_URL"
    echo ""
    echo "Results:"
    echo "  Passed: $PASSED"
    echo "  Failed: $FAILED"
    echo "  Warnings: $WARNINGS"
    echo "  Total: $TOTAL"
} > "$REPORT_FILE"

echo "Report saved to: $REPORT_FILE"
