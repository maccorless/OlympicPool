#!/usr/bin/env python3
"""
Initialize Railway database from production dump.
Run this script on Railway to import data.
"""
import os
import sqlite3

def init_database():
    """Initialize database from schema and import production data."""

    # Get database path from environment
    db_dir = os.getenv('DATABASE_DIR', '/app/instance')
    db_path = os.path.join(db_dir, 'medal_pool.db')

    print(f"Database path: {db_path}")

    # Ensure directory exists
    os.makedirs(db_dir, exist_ok=True)

    # Read production dump
    dump_file = 'production_dump.sql'
    if not os.path.exists(dump_file):
        print(f"ERROR: {dump_file} not found!")
        print(f"Current directory: {os.getcwd()}")
        print(f"Files: {os.listdir('.')}")
        return False

    print(f"Reading SQL dump from {dump_file}...")
    with open(dump_file, 'r') as f:
        sql_dump = f.read()

    # Import into database
    print(f"Importing into {db_path}...")
    conn = sqlite3.connect(db_path)
    conn.executescript(sql_dump)
    conn.commit()

    # Verify
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM picks")
    pick_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM countries")
    country_count = cursor.fetchone()[0]

    conn.close()

    print(f"✅ Database initialized successfully!")
    print(f"   Users: {user_count}")
    print(f"   Picks: {pick_count}")
    print(f"   Countries: {country_count}")

    return True

if __name__ == '__main__':
    init_database()
