#!/usr/bin/env python3
"""
Script to add Cris Krachon entry to the Corless contest.
Usage: python add_cris_entry.py
"""
import sqlite3
import sys
import os
from datetime import datetime

# Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'medal_pool.db')
EVENT_SLUG = 'mc26'
CONTEST_SLUG = 'corless'

# User data
USER_EMAIL = 'cris@krachon.com'
USER_NAME = 'Cris Krachon'
USER_PHONE = '+1.404.808.3057'
TEAM_NAME = 'East Rivers'

# Picks
PICKS = ['GER', 'CAN', 'SWE', 'CHN', 'FIN']


def main():
    # Connect to database
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    db = conn.cursor()

    try:
        # Get event_id
        event = db.execute('SELECT id FROM events WHERE slug = ?', [EVENT_SLUG]).fetchone()
        if not event:
            print(f"Error: Event '{EVENT_SLUG}' not found")
            sys.exit(1)
        event_id = event['id']
        print(f"Found event: {EVENT_SLUG} (id={event_id})")

        # Get contest_id
        contest = db.execute('''
            SELECT id FROM contest WHERE slug = ? AND event_id = ?
        ''', [CONTEST_SLUG, event_id]).fetchone()
        if not contest:
            print(f"Error: Contest '{CONTEST_SLUG}' not found in event '{EVENT_SLUG}'")
            sys.exit(1)
        contest_id = contest['id']
        print(f"Found contest: {CONTEST_SLUG} (id={contest_id})")

        # Create or update user
        existing_user = db.execute('SELECT id FROM users WHERE email = ?', [USER_EMAIL]).fetchone()

        if existing_user:
            user_id = existing_user['id']
            print(f"User exists with id={user_id}, updating...")
            db.execute('''
                UPDATE users
                SET name = ?, team_name = ?, phone_number = ?
                WHERE id = ?
            ''', [USER_NAME, TEAM_NAME, USER_PHONE, user_id])
        else:
            print("Creating new user...")
            db.execute('''
                INSERT INTO users (email, phone_number, name, team_name, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', [USER_EMAIL, USER_PHONE, USER_NAME, TEAM_NAME])
            user_id = db.lastrowid
            print(f"Created user with id={user_id}")

        # Register user in contest (if not already)
        existing_registration = db.execute('''
            SELECT 1 FROM user_contest_info WHERE user_id = ? AND contest_id = ?
        ''', [user_id, contest_id]).fetchone()

        if not existing_registration:
            print("Registering user in contest...")
            db.execute('''
                INSERT INTO user_contest_info (user_id, contest_id, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', [user_id, contest_id])
            print("User registered in contest")
        else:
            print("User already registered in contest")

        # Delete existing picks for this user in this contest
        print("Removing any existing picks...")
        db.execute('''
            DELETE FROM picks WHERE user_id = ? AND contest_id = ?
        ''', [user_id, contest_id])

        # Insert new picks
        print(f"Adding picks: {', '.join(PICKS)}")
        for country_code in PICKS:
            db.execute('''
                INSERT INTO picks (user_id, country_code, contest_id, event_id, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', [user_id, country_code, contest_id, event_id])
            print(f"  Added: {country_code}")

        # Commit all changes
        conn.commit()
        print("\n✅ SUCCESS! Entry created/updated for Cris Krachon")
        print(f"   Email: {USER_EMAIL}")
        print(f"   Team: {TEAM_NAME}")
        print(f"   Picks: {', '.join(PICKS)}")

    except sqlite3.Error as e:
        print(f"\n❌ Database error: {e}")
        conn.rollback()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
