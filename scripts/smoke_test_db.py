#!/usr/bin/env python3
"""
Smoke test for database schema initialization.
Validates Step 1: schema.sql, db initialization code.

Usage: python scripts/smoke_test_db.py
Exit codes: 0 = success, 1 = failure
"""
import os
import sys
import sqlite3
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def log(msg):
    """Print status message."""
    print(f"[smoke_test_db] {msg}")


def fail(msg):
    """Print error and exit with failure code."""
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


def apply_schema(db_path):
    """Apply schema.sql to database (same as app does)."""
    schema_path = project_root / 'schema.sql'

    if not schema_path.exists():
        fail(f"schema.sql not found at {schema_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        with open(schema_path, 'r') as f:
            conn.executescript(f.read())
        conn.commit()
        log("✓ Applied schema.sql")
    except Exception as e:
        fail(f"Failed to apply schema: {e}")
    finally:
        conn.close()


def test_tables_exist(db_path):
    """Assert all required tables exist."""
    required_tables = ['contest', 'users', 'countries', 'picks', 'medals', 'tokens', 'system_meta']

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        missing = [t for t in required_tables if t not in tables]

        if missing:
            fail(f"Missing tables: {', '.join(missing)}")

        log(f"✓ All required tables exist: {', '.join(required_tables)}")
    finally:
        conn.close()


def test_contest_initialization(db_path):
    """Test contest table is initialized with default row."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM contest WHERE id = 1')
        contest = cursor.fetchone()

        if not contest:
            fail("Contest table not initialized with default row (id=1)")

        # Verify required fields
        if contest['state'] != 'setup':
            fail(f"Contest state should be 'setup', got '{contest['state']}'")

        if contest['budget'] != 200:
            fail(f"Contest budget should be 200, got {contest['budget']}")

        if contest['max_countries'] != 10:
            fail(f"Contest max_countries should be 10, got {contest['max_countries']}")

        log(f"✓ Contest initialized: state={contest['state']}, budget={contest['budget']}, max_countries={contest['max_countries']}")
    finally:
        conn.close()


def test_insert_select(db_path):
    """Test trivial insert/select on system_meta."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Insert test data
        cursor.execute(
            'INSERT INTO system_meta (key, value) VALUES (?, ?)',
            ['test_key', 'test_value']
        )
        conn.commit()

        # Select it back
        cursor.execute('SELECT value FROM system_meta WHERE key = ?', ['test_key'])
        row = cursor.fetchone()

        if not row:
            fail("Failed to retrieve inserted system_meta row")

        if row['value'] != 'test_value':
            fail(f"system_meta value mismatch: expected 'test_value', got '{row['value']}'")

        log("✓ Insert/select test passed on system_meta")
    finally:
        conn.close()


def test_user_id_autoincrement(db_path):
    """Test that users.id is INTEGER AUTOINCREMENT."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Get table schema
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
        schema = cursor.fetchone()[0]

        if 'INTEGER PRIMARY KEY AUTOINCREMENT' not in schema:
            fail("users.id must be INTEGER PRIMARY KEY AUTOINCREMENT")

        log("✓ users.id is INTEGER PRIMARY KEY AUTOINCREMENT")
    finally:
        conn.close()


def test_tokens_table_structure(db_path):
    """Test that tokens table uses token_hash + user_id."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Get column info
        cursor.execute("PRAGMA table_info(tokens)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}  # name: type

        if 'token_hash' not in columns:
            fail("tokens table must have token_hash column")

        if 'user_id' not in columns:
            fail("tokens table must have user_id column")

        if 'email' in columns:
            fail("tokens table should not have email column (should use user_id instead)")

        log("✓ tokens table structure correct (token_hash + user_id)")
    finally:
        conn.close()


def test_no_is_admin_field(db_path):
    """Test that users table does NOT have is_admin field."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'is_admin' in columns:
            fail("users table should NOT have is_admin field (admin determined by ADMIN_EMAILS config)")

        log("✓ users table does not have is_admin field")
    finally:
        conn.close()


def main():
    """Run all smoke tests."""
    log("Starting database smoke tests...")

    # Create temporary database
    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
        temp_db = f.name

    try:
        log(f"Using temporary database: {temp_db}")

        # Run tests
        apply_schema(temp_db)
        test_tables_exist(temp_db)
        test_contest_initialization(temp_db)
        test_insert_select(temp_db)
        test_user_id_autoincrement(temp_db)
        test_tokens_table_structure(temp_db)
        test_no_is_admin_field(temp_db)

        log("✅ All smoke tests passed!")
        return 0

    except Exception as e:
        fail(f"Unexpected error: {e}")

    finally:
        # Cleanup
        if os.path.exists(temp_db):
            os.unlink(temp_db)
            log(f"Cleaned up temporary database")


if __name__ == '__main__':
    sys.exit(main())
