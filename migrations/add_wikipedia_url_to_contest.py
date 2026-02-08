#!/usr/bin/env python3
"""Migration: Add wikipedia_medal_url column to contest table"""
import sqlite3
import sys
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'instance')
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
        cursor.execute("PRAGMA table_info(contest)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'wikipedia_medal_url' in columns:
            print("✅ Column 'wikipedia_medal_url' already exists.")
            return

        # Add the column
        print("Adding column 'wikipedia_medal_url' to contest table...")
        cursor.execute("ALTER TABLE contest ADD COLUMN wikipedia_medal_url TEXT")

        # Set default URL for Milano Cortina 2026
        print("Setting Wikipedia URL...")
        cursor.execute("""
            UPDATE contest
            SET wikipedia_medal_url = 'https://en.wikipedia.org/wiki/2026_Winter_Olympics_medal_table'
            WHERE id = 1
        """)

        conn.commit()
        print("✅ Migration completed successfully!")

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
