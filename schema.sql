-- ============================================================================
-- OLYMPIC MEDAL POOL - DATABASE SCHEMA (Multi-Contest/Multi-Event)
-- ============================================================================
-- This is the authoritative schema. See CLAUDE.md for documentation.
-- ============================================================================

-- Events (Olympic Games)
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,  -- "Milano Cortina 2026"
    slug TEXT UNIQUE NOT NULL,  -- "milano-2026" for URLs
    description TEXT,  -- "XXV Winter Olympic Games - Italy"
    start_date TEXT NOT NULL,  -- ISO8601 UTC timestamp
    end_date TEXT NOT NULL,  -- ISO8601 UTC timestamp
    olympics_api_slug TEXT,  -- Olympics.com API slug (e.g., "wmr-owg2026") for auto-refresh
    wikipedia_medal_url TEXT,  -- Wikipedia medal table URL for scraping (e.g., "https://en.wikipedia.org/wiki/2026_Winter_Olympics_medal_table")
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Contest configuration (multiple contests per event)
CREATE TABLE contest (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    slug TEXT NOT NULL,  -- "office-pool", "family-pool"
    name TEXT NOT NULL,  -- "Office Pool 2026"
    description TEXT,  -- "DTEC office competition" (shown on home page)
    state TEXT NOT NULL DEFAULT 'setup' CHECK (state IN ('setup', 'open', 'locked', 'complete')),
    budget INTEGER NOT NULL DEFAULT 200,
    max_countries INTEGER NOT NULL DEFAULT 10,
    deadline TEXT NOT NULL,  -- ISO8601 UTC timestamp
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, slug)  -- Slug unique within event
);

-- Users (global across all contests)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL CHECK (email LIKE '%@%'),
    phone_number TEXT NOT NULL,  -- E.164 format: +12065551234 (NOT unique - allows multiple accounts per phone)
    name TEXT NOT NULL,
    team_name TEXT NOT NULL,  -- User's fantasy team name (global across contests)
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- User-Contest relationship (tracks which users are in which contests)
CREATE TABLE user_contest_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    contest_id INTEGER NOT NULL REFERENCES contest(id) ON DELETE CASCADE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, contest_id)
);

-- Countries (reference data, per-event)
CREATE TABLE countries (
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    code TEXT NOT NULL,  -- IOC 3-letter code (NOR, GER, SUI)
    iso_code TEXT NOT NULL,  -- ISO 2-letter code (NO, DE, CH) for flag URLs
    name TEXT NOT NULL,
    expected_points INTEGER NOT NULL,  -- Projected points (reference only)
    cost INTEGER NOT NULL,  -- Draft cost
    is_active INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (event_id, code)
);

-- User picks (per-contest)
CREATE TABLE picks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contest_id INTEGER NOT NULL REFERENCES contest(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id INTEGER NOT NULL,  -- Denormalized from contest for easier queries
    country_code TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(contest_id, user_id, country_code),
    FOREIGN KEY (event_id, country_code) REFERENCES countries(event_id, code)
);

-- Actual medals (updated during Games, per-event)
CREATE TABLE medals (
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    country_code TEXT NOT NULL,
    gold INTEGER NOT NULL DEFAULT 0,
    silver INTEGER NOT NULL DEFAULT 0,
    bronze INTEGER NOT NULL DEFAULT 0,
    points INTEGER NOT NULL DEFAULT 0,  -- Calculated: gold*3 + silver*2 + bronze
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (event_id, country_code),
    FOREIGN KEY (event_id, country_code) REFERENCES countries(event_id, code)
);

-- OTP codes for SMS verification (global device verification, not contest-specific)
CREATE TABLE otp_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code_hash TEXT NOT NULL,  -- SHA-256 hash of 4-digit code
    expires_at TEXT NOT NULL,  -- ISO8601 UTC (10 minutes from creation)
    used_at TEXT,  -- Set when consumed (single-use)
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- System metadata (key-value store for refresh timestamps, etc.)
CREATE TABLE system_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_contest_event_slug ON contest(event_id, slug);
CREATE INDEX idx_countries_event ON countries(event_id, code);
CREATE INDEX idx_medals_event ON medals(event_id, country_code);
CREATE INDEX idx_picks_contest_user ON picks(contest_id, user_id);
CREATE INDEX idx_picks_event_country ON picks(event_id, country_code);
CREATE INDEX idx_user_contest_info ON user_contest_info(user_id, contest_id);
CREATE INDEX idx_otp_user_created ON otp_codes(user_id, created_at);
CREATE INDEX idx_otp_expires ON otp_codes(expires_at);

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Create default event: Milano Cortina 2026
INSERT OR IGNORE INTO events (id, name, slug, description, start_date, end_date)
VALUES (1, 'Milano Cortina 2026', 'milano-2026', 'XXV Winter Olympic Games', '2026-02-06', '2026-02-22');

-- Create default contest
-- Deadline: Feb 4, 2026 at 18:00 CET (17:00 UTC)
INSERT OR IGNORE INTO contest (id, event_id, slug, name, description, state, budget, max_countries, deadline)
VALUES (1, 1, 'default', 'XXV Winter Olympic Games', 'Main contest pool', 'setup', 200, 10, '2026-02-04T17:00:00Z');

-- Create administrator account (ken@corless.com)
-- Phone placeholder - user must provide real phone on first login
INSERT OR IGNORE INTO users (id, email, phone_number, name, team_name)
VALUES (1, 'ken@corless.com', '+10000000000', 'Ken Corless', 'Admin Team');

-- Register administrator for default contest
INSERT OR IGNORE INTO user_contest_info (user_id, contest_id)
VALUES (1, 1);
