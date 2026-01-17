-- ============================================================================
-- OLYMPIC MEDAL POOL - DATABASE SCHEMA
-- ============================================================================
-- This is the authoritative schema. See CLAUDE.md for documentation.
-- ============================================================================

-- Contest configuration (single row)
CREATE TABLE contest (
    id INTEGER PRIMARY KEY CHECK (id = 1),  -- Enforce single row
    name TEXT NOT NULL DEFAULT 'XXV Winter Olympic Games',
    state TEXT NOT NULL DEFAULT 'setup' CHECK (state IN ('setup', 'open', 'locked', 'complete')),
    budget INTEGER NOT NULL DEFAULT 200,
    max_countries INTEGER NOT NULL DEFAULT 10,
    deadline TEXT NOT NULL,  -- ISO8601 UTC timestamp
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Users (no is_admin field - determined by ADMIN_EMAILS config)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL CHECK (email LIKE '%@%'),
    phone_number TEXT UNIQUE NOT NULL,  -- E.164 format: +12065551234
    name TEXT NOT NULL,
    team_name TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Countries (reference data, pre-populated from countries.sql)
CREATE TABLE countries (
    code TEXT PRIMARY KEY,  -- IOC 3-letter code (NOR, GER, SUI)
    iso_code TEXT NOT NULL,  -- ISO 2-letter code (NO, DE, CH) for flag URLs
    name TEXT NOT NULL,
    expected_points INTEGER NOT NULL,  -- Projected points (reference only)
    cost INTEGER NOT NULL,  -- Draft cost
    is_active INTEGER NOT NULL DEFAULT 1
);

-- User picks
CREATE TABLE picks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    country_code TEXT NOT NULL REFERENCES countries(code),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, country_code)
);

-- Actual medals (updated during Games)
CREATE TABLE medals (
    country_code TEXT PRIMARY KEY REFERENCES countries(code),
    gold INTEGER NOT NULL DEFAULT 0,
    silver INTEGER NOT NULL DEFAULT 0,
    bronze INTEGER NOT NULL DEFAULT 0,
    points INTEGER NOT NULL DEFAULT 0,  -- Calculated: gold*3 + silver*2 + bronze
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- OTP codes for new device authentication (SMS-based)
CREATE TABLE otp_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code_hash TEXT NOT NULL,  -- SHA-256 hash of 6-digit code
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

-- Indexes
CREATE INDEX idx_picks_user ON picks(user_id);
CREATE INDEX idx_otp_user_created ON otp_codes(user_id, created_at);  -- Compound index for rate limiting
CREATE INDEX idx_otp_expires ON otp_codes(expires_at);

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Initialize contest with default values (idempotent)
-- Deadline: Feb 4, 2026 at 18:00 CET (17:00 UTC)
INSERT OR IGNORE INTO contest (id, name, state, budget, max_countries, deadline)
VALUES (1, 'XXV Winter Olympic Games', 'setup', 200, 10, '2026-02-04T17:00:00Z');
