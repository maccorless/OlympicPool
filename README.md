# Olympic Medal Pool

Fantasy-sports-style web application for predicting Olympic medal outcomes. Users draft countries within a budget and earn points based on actual medal results.

**Features:**
- Multi-event support (Milano Cortina 2026, LA 2028, etc.)
- Multi-contest support (office pool, friends pool, etc.)
- SMS OTP authentication via Twilio
- Real-time leaderboards with sortable columns
- Contest admin and global admin roles
- Mobile-responsive design
- Automatic medal updates from Wikipedia

## Local Development

### Setup

```bash
# Clone repository
git clone <repo>
cd OlympicPool2

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from example
cp .env.example .env

# Edit .env with your settings (see Environment Variables below)

# Initialize database
flask init-db
```

### Run

```bash
source .venv/bin/activate
export FLASK_APP=app

# Run on port 5001 (port 5000 conflicts with macOS AirPlay)
flask run --port 5001
```

App will be available at: http://localhost:5001

### Testing Login

Magic links are printed to the console in dev mode (no RESEND_API_KEY set).

You can also generate a magic link for any user:

```bash
python3 scripts/get_magic_link.py <email>
```

### Testing

```bash
# Database smoke test
python3 scripts/smoke_test_db.py

# Auth flow test
python3 scripts/test_auth.py

# Wikipedia scraper test
python3 test_wikipedia_scraper.py
```

## Medal Data Updates

The app supports three methods for updating medal counts:

1. **Wikipedia Auto-Scraping** - One-click refresh from Wikipedia medal tables (recommended)
2. **Bulk Paste** - Copy/paste medal data from Excel or spreadsheets
3. **Individual Entry** - Manually type in medal counts per country

Admins can use any method from the medal entry page. See `WIKIPEDIA_SCRAPING.md` for scraping details.

## Environment Variables

The following environment variables are required (see `.env.example` for details):

**Required:**
- `FLASK_SECRET_KEY` - Secret key for sessions (min 32 chars)
- `BASE_URL` - Base URL of the application
- `ADMIN_EMAILS` - Comma-separated list of contest admin emails
- `GLOBAL_ADMIN_EMAILS` - Comma-separated list of global admin emails
- `TWILIO_ACCOUNT_SID` - Twilio account SID
- `TWILIO_AUTH_TOKEN` - Twilio auth token
- `TWILIO_VERIFY_SERVICE_SID` - Twilio Verify service SID

**Optional:**
- `RESEND_API_KEY` - Resend API key for email (optional)
- `NO_SMS_MODE=True` - Bypass SMS for local dev
- `NO_EMAIL_MODE=True` - Print emails to console for local dev
- `FLASK_DEBUG=True` - Enable debug mode (local dev only)
- `SESSION_COOKIE_SECURE=False` - Set to True in production (requires HTTPS)

**Production:**
Generate a secure secret key:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Deployment

See `DEPLOYMENT.md` for complete Railway deployment instructions.

**Quick steps:**
1. Create Railway project
2. Add database volume at `/app/instance`
3. Configure environment variables
4. Deploy from GitHub or Railway CLI
5. Configure custom domain (optional)

The application uses:
- Dockerfile for containerized deployment
- Gunicorn as WSGI server
- SQLite with persistent volume
- Automatic database initialization on first run

## Tech Stack

- **Backend**: Flask 3.x (Python 3.11+)
- **Database**: SQLite (no ORM, raw SQL)
- **Frontend**: Jinja2 templates + HTMX + Tailwind CSS
- **Auth**: Passwordless magic links (Resend API)

## Project Structure

```
OlympicPool2/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration from env vars
│   ├── db.py                # Database helpers
│   ├── decorators.py        # Auth & admin decorators
│   ├── routes/              # Route modules
│   │   ├── events.py        # Contest selector
│   │   ├── auth.py          # SMS OTP authentication
│   │   ├── draft.py         # Country draft picker
│   │   ├── leaderboard.py   # Leaderboard & team views
│   │   ├── admin.py         # Contest admin routes
│   │   └── global_admin.py  # Global admin routes
│   ├── services/            # External services
│   │   ├── sms.py           # Twilio SMS OTP
│   │   └── email.py         # Resend email (optional)
│   └── templates/           # Jinja2 templates
├── schema.sql               # Database schema (authoritative)
├── scripts/                 # Development tools
├── instance/                # SQLite database (gitignored)
├── Dockerfile               # Docker container config
├── start.sh                 # Startup script for Railway
├── railway.toml             # Railway deployment config
├── requirements.txt         # Python dependencies
└── .env.example             # Example environment variables
```

## Documentation

- `CLAUDE.md` - Complete implementation guide and technical decisions
- `DEPLOYMENT.md` - Railway deployment instructions
- `.env.example` - Environment variable reference
