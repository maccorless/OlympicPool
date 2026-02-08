#!/usr/bin/env python3
"""
Migration: Add wikipedia_medal_url column to events table
"""
import sqlite3
import sys
import os

# Database path
DB_PATH = os.getenv('DATABASE_DIR', 'instance')
DB_FILE = os.path.join(DB_PATH, 'medal_pool.db')

def main():
    print(f"Connecting to database: {DB_FILE}")

    if not os.path.exists(DB_FILE):
        print(f"ERROR: Database not found at {DB_FILE}")
        sys.exit(1)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(events)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'wikipedia_medal_url' in columns:
            print("✅ Column 'wikipedia_medal_url' already exists. Nothing to do.")
            return

        # Add the column
        print("Adding column 'wikipedia_medal_url' to events table...")
        cursor.execute("""
            ALTER TABLE events ADD COLUMN wikipedia_medal_url TEXT
        """)

        # Set the URL for mc26 event (Milano Cortina 2026)
        print("Setting Wikipedia URL for mc26 event...")
        cursor.execute("""
            UPDATE events
            SET wikipedia_medal_url = 'https://en.wikipedia.org/wiki/2026_Winter_Olympics_medal_table'
            WHERE slug = 'mc26'
        """)

        conn.commit()
        print("✅ Migration completed successfully!")

        # Verify
        cursor.execute("SELECT slug, wikipedia_medal_url FROM events")
        results = cursor.fetchall()
        print("\nCurrent events with Wikipedia URLs:")
        for row in results:
            print(f"  {row[0]}: {row[1] or '(not set)'}")

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
