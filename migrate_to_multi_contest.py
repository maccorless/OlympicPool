#!/usr/bin/env python3
"""
Migration script: Single-contest → Multi-contest/Multi-event

This script migrates the existing database from the single-contest model to
support multiple events and multiple contests per event.

Usage:
    python migrate_to_multi_contest.py [--db path/to/database.db]

If --db is not specified, migrates the default instance/medal_pool.db

IMPORTANT: This script creates backups before migration. If migration fails,
tables can be restored from *_backup tables.
"""
import sqlite3
import sys
import os
import argparse
from datetime import datetime, timezone


def backup_tables(conn):
    """Create backup copies of all tables before migration."""
    print("Creating table backups...")
    cursor = conn.cursor()

    tables = ['contest', 'countries', 'medals', 'picks', 'users', 'tokens']

    for table in tables:
        # Check if table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if cursor.fetchone():
            # Drop backup if it exists
            cursor.execute(f"DROP TABLE IF EXISTS {table}_backup")
            # Create backup
            cursor.execute(f"CREATE TABLE {table}_backup AS SELECT * FROM {table}")
            print(f"  ✓ Backed up {table} → {table}_backup")

    conn.commit()


def rollback_from_backup(conn):
    """Restore tables from backup in case of failure."""
    print("\n⚠️  Rolling back changes...")
    cursor = conn.cursor()

    tables = ['contest', 'countries', 'medals', 'picks', 'users', 'tokens']

    for table in tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}_backup'")
        if cursor.fetchone():
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            cursor.execute(f"ALTER TABLE {table}_backup RENAME TO {table}")
            print(f"  ✓ Restored {table} from backup")

    conn.commit()
    print("Rollback complete. Database restored to pre-migration state.")


def migrate_database(db_path):
    """Execute the full migration."""
    print(f"Starting migration of {db_path}")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}\n")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Step 0: Create backups
        backup_tables(conn)

        # Step 1: Create events table
        print("\n1. Creating events table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                description TEXT,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("  ✓ events table created")

        # Step 2: Insert Milano Cortina 2026 event
        print("\n2. Inserting Milano Cortina 2026 event...")
        cursor.execute('''
            INSERT INTO events (id, name, slug, description, start_date, end_date)
            VALUES (1, 'Milano Cortina 2026', 'milano-2026', 'XXV Winter Olympic Games', '2026-02-06', '2026-02-22')
        ''')
        print("  ✓ Event inserted (id=1, slug='milano-2026')")

        # Step 3: Migrate contest table
        print("\n3. Migrating contest table...")
        cursor.execute('''
            CREATE TABLE contest_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
                slug TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                state TEXT NOT NULL DEFAULT 'setup' CHECK (state IN ('setup', 'open', 'locked', 'complete')),
                budget INTEGER NOT NULL DEFAULT 200,
                max_countries INTEGER NOT NULL DEFAULT 10,
                deadline TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(event_id, slug)
            )
        ''')

        cursor.execute('''
            INSERT INTO contest_new (id, event_id, slug, name, description, state, budget, max_countries, deadline, created_at, updated_at)
            SELECT id, 1 as event_id, 'default' as slug, name, 'Main contest pool' as description, state, budget, max_countries, deadline, created_at, updated_at
            FROM contest WHERE id = 1
        ''')

        cursor.execute('DROP TABLE contest')
        cursor.execute('ALTER TABLE contest_new RENAME TO contest')
        print("  ✓ contest table migrated (event_id=1, slug='default')")

        # Step 4: Migrate countries table
        print("\n4. Migrating countries table...")
        cursor.execute('''
            CREATE TABLE countries_new (
                event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
                code TEXT NOT NULL,
                iso_code TEXT NOT NULL,
                name TEXT NOT NULL,
                expected_points INTEGER NOT NULL,
                cost INTEGER NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (event_id, code)
            )
        ''')

        cursor.execute('''
            INSERT INTO countries_new (event_id, code, iso_code, name, expected_points, cost, is_active)
            SELECT 1 as event_id, code, iso_code, name, expected_points, cost, is_active
            FROM countries
        ''')

        count = cursor.execute('SELECT COUNT(*) FROM countries_new').fetchone()[0]

        cursor.execute('DROP TABLE countries')
        cursor.execute('ALTER TABLE countries_new RENAME TO countries')
        print(f"  ✓ countries table migrated ({count} countries → event_id=1)")

        # Step 5: Migrate medals table
        print("\n5. Migrating medals table...")
        cursor.execute('''
            CREATE TABLE medals_new (
                event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
                country_code TEXT NOT NULL,
                gold INTEGER NOT NULL DEFAULT 0,
                silver INTEGER NOT NULL DEFAULT 0,
                bronze INTEGER NOT NULL DEFAULT 0,
                points INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (event_id, country_code),
                FOREIGN KEY (event_id, country_code) REFERENCES countries(event_id, code)
            )
        ''')

        cursor.execute('''
            INSERT INTO medals_new (event_id, country_code, gold, silver, bronze, points, updated_at)
            SELECT 1 as event_id, country_code, gold, silver, bronze, points, updated_at
            FROM medals
        ''')

        count = cursor.execute('SELECT COUNT(*) FROM medals_new').fetchone()[0]

        cursor.execute('DROP TABLE medals')
        cursor.execute('ALTER TABLE medals_new RENAME TO medals')
        print(f"  ✓ medals table migrated ({count} medal records → event_id=1)")

        # Step 6: Migrate picks table
        print("\n6. Migrating picks table...")
        cursor.execute('''
            CREATE TABLE picks_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contest_id INTEGER NOT NULL REFERENCES contest(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                event_id INTEGER NOT NULL,
                country_code TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(contest_id, user_id, country_code),
                FOREIGN KEY (event_id, country_code) REFERENCES countries(event_id, code)
            )
        ''')

        cursor.execute('''
            INSERT INTO picks_new (id, contest_id, user_id, event_id, country_code, created_at)
            SELECT id, 1 as contest_id, user_id, 1 as event_id, country_code, created_at
            FROM picks
        ''')

        count = cursor.execute('SELECT COUNT(*) FROM picks_new').fetchone()[0]

        cursor.execute('DROP TABLE picks')
        cursor.execute('ALTER TABLE picks_new RENAME TO picks')
        print(f"  ✓ picks table migrated ({count} picks → contest_id=1, event_id=1)")

        # Step 7: Create user_contest_info table
        print("\n7. Creating user_contest_info table...")
        cursor.execute('''
            CREATE TABLE user_contest_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                contest_id INTEGER NOT NULL REFERENCES contest(id) ON DELETE CASCADE,
                team_name TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, contest_id)
            )
        ''')

        cursor.execute('''
            INSERT INTO user_contest_info (user_id, contest_id, team_name, created_at)
            SELECT id, 1, team_name, created_at FROM users
        ''')

        count = cursor.execute('SELECT COUNT(*) FROM user_contest_info').fetchone()[0]
        print(f"  ✓ user_contest_info created ({count} entries for contest_id=1)")

        # Step 8: Migrate users table (remove team_name)
        print("\n8. Removing team_name from users table...")
        cursor.execute('''
            CREATE TABLE users_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL CHECK (email LIKE '%@%'),
                name TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            INSERT INTO users_new (id, email, name, created_at)
            SELECT id, email, name, created_at FROM users
        ''')

        count = cursor.execute('SELECT COUNT(*) FROM users_new').fetchone()[0]

        cursor.execute('DROP TABLE users')
        cursor.execute('ALTER TABLE users_new RENAME TO users')
        print(f"  ✓ users table updated ({count} users, team_name moved to user_contest_info)")

        # Step 9: Add contest_id to tokens
        print("\n9. Adding contest_id to tokens table...")
        cursor.execute('ALTER TABLE tokens ADD COLUMN contest_id INTEGER REFERENCES contest(id) ON DELETE CASCADE')
        cursor.execute('UPDATE tokens SET contest_id = 1 WHERE contest_id IS NULL')

        count = cursor.execute('SELECT COUNT(*) FROM tokens').fetchone()[0]
        print(f"  ✓ tokens updated ({count} tokens → contest_id=1)")

        # Step 10: Drop old indexes
        print("\n10. Updating indexes...")
        cursor.execute('DROP INDEX IF EXISTS idx_picks_user')
        cursor.execute('DROP INDEX IF EXISTS idx_tokens_user_created')
        print("  ✓ Old indexes dropped")

        # Step 11: Create new indexes
        cursor.execute('CREATE INDEX idx_contest_event_slug ON contest(event_id, slug)')
        cursor.execute('CREATE INDEX idx_countries_event ON countries(event_id, code)')
        cursor.execute('CREATE INDEX idx_medals_event ON medals(event_id, country_code)')
        cursor.execute('CREATE INDEX idx_picks_contest_user ON picks(contest_id, user_id)')
        cursor.execute('CREATE INDEX idx_picks_event_country ON picks(event_id, country_code)')
        cursor.execute('CREATE INDEX idx_user_contest_info ON user_contest_info(user_id, contest_id)')
        cursor.execute('CREATE INDEX idx_tokens_contest_user ON tokens(contest_id, user_id, created_at)')
        print("  ✓ New indexes created")

        # Commit all changes
        conn.commit()

        # Verify migration
        print("\n" + "="*60)
        print("MIGRATION VERIFICATION")
        print("="*60)

        event_count = cursor.execute('SELECT COUNT(*) FROM events').fetchone()[0]
        contest_count = cursor.execute('SELECT COUNT(*) FROM contest').fetchone()[0]
        country_count = cursor.execute('SELECT COUNT(*) FROM countries').fetchone()[0]
        user_count = cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        uci_count = cursor.execute('SELECT COUNT(*) FROM user_contest_info').fetchone()[0]
        pick_count = cursor.execute('SELECT COUNT(*) FROM picks').fetchone()[0]

        print(f"Events:            {event_count}")
        print(f"Contests:          {contest_count}")
        print(f"Countries:         {country_count}")
        print(f"Users:             {user_count}")
        print(f"User-Contest Info: {uci_count}")
        print(f"Picks:             {pick_count}")

        print("\n" + "="*60)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nBackup tables (*_backup) are preserved.")
        print("You can drop them once you've verified the migration:")
        print("  DROP TABLE contest_backup;")
        print("  DROP TABLE countries_backup;")
        print("  DROP TABLE medals_backup;")
        print("  DROP TABLE picks_backup;")
        print("  DROP TABLE users_backup;")
        print("  DROP TABLE tokens_backup;")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        rollback_from_backup(conn)
        conn.close()
        sys.exit(1)

    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='Migrate database to multi-contest schema')
    parser.add_argument('--db', default='instance/medal_pool.db',
                      help='Path to database file (default: instance/medal_pool.db)')
    args = parser.parse_args()

    db_path = args.db

    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)

    # Confirm migration
    print(f"This will migrate: {db_path}")
    print("\nThe migration will:")
    print("  - Add multi-event/multi-contest support")
    print("  - Create backup tables for safety")
    print("  - Preserve all existing data")
    print()

    response = input("Continue? [y/N]: ")
    if response.lower() != 'y':
        print("Migration cancelled.")
        sys.exit(0)

    migrate_database(db_path)


if __name__ == '__main__':
    main()
