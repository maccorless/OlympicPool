#!/usr/bin/env python3
"""
One-time migration script to normalize existing emails to lowercase.

This ensures case-insensitive email handling for all existing users.
Run this once after deploying the email normalization changes.

Usage:
    python migrate_lowercase_emails.py
"""
import sqlite3
import os
import sys

# Get database path from environment or use default
DATABASE_DIR = os.getenv('DATABASE_DIR', os.path.join(os.path.dirname(__file__), 'instance'))
DATABASE = os.path.join(DATABASE_DIR, 'medal_pool.db')

def migrate_emails():
    """Normalize all existing emails to lowercase."""
    if not os.path.exists(DATABASE):
        print(f"Error: Database not found at {DATABASE}")
        sys.exit(1)

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Get all users
        users = cursor.execute('SELECT id, email FROM users').fetchall()

        if not users:
            print("No users found in database.")
            return

        print(f"Found {len(users)} users. Normalizing emails to lowercase...")

        updated_count = 0
        for user in users:
            original_email = user['email']
            lowercase_email = original_email.lower()

            if original_email != lowercase_email:
                print(f"  Updating: {original_email} -> {lowercase_email}")
                cursor.execute('UPDATE users SET email = ? WHERE id = ?',
                             [lowercase_email, user['id']])
                updated_count += 1
            else:
                print(f"  Already lowercase: {original_email}")

        conn.commit()

        print(f"\nMigration complete!")
        print(f"  Total users: {len(users)}")
        print(f"  Updated: {updated_count}")
        print(f"  Already lowercase: {len(users) - updated_count}")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Email Normalization Migration")
    print("=" * 60)
    migrate_emails()
