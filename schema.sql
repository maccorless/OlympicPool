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
    name TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- User-Contest relationship (team names are per-contest)
CREATE TABLE user_contest_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    contest_id INTEGER NOT NULL REFERENCES contest(id) ON DELETE CASCADE,
    team_name TEXT NOT NULL,  -- User's fantasy team name for this contest
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

-- Auth tokens (magic links, stores token_hash + contest_id)
CREATE TABLE tokens (
    token_hash TEXT PRIMARY KEY,  -- SHA-256 hash of token
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    contest_id INTEGER REFERENCES contest(id) ON DELETE CASCADE,
    token_type TEXT NOT NULL DEFAULT 'magic_link' CHECK (token_type = 'magic_link'),
    expires_at TEXT NOT NULL,  -- ISO8601 UTC
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
CREATE INDEX idx_tokens_contest_user ON tokens(contest_id, user_id, created_at);
CREATE INDEX idx_tokens_expires ON tokens(expires_at);

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
