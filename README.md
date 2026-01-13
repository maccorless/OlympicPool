# Olympic Medal Pool

Fantasy-sports-style web application for Milano Cortina 2026 Winter Olympics.

## Local Development

### Setup

```bash
# Clone repository
git clone <repo>
cd OlympicPool

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from example
cp .env.example .env

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
```

## Tech Stack

- **Backend**: Flask 3.x (Python 3.11+)
- **Database**: SQLite (no ORM, raw SQL)
- **Frontend**: Jinja2 templates + HTMX + Tailwind CSS
- **Auth**: Passwordless magic links (Resend API)

## Project Structure

```
OlympicPool/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration
│   ├── db.py                # Database helpers
│   ├── decorators.py        # Auth decorators
│   ├── routes/              # Route modules
│   └── templates/           # Jinja2 templates
├── schema.sql               # Database schema
├── scripts/                 # Development tools
├── instance/                # SQLite database
└── requirements.txt
```

## Documentation

See `CLAUDE.md` for complete implementation guide.
