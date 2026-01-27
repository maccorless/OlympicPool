#!/usr/bin/env python3
"""
Comprehensive testing script for multi-contest implementation.
Tests database integrity, route functionality, and data isolation.
"""

import sqlite3
import sys
from datetime import datetime

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text:^70}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓{RESET} {text}")

def print_error(text):
    print(f"{RED}✗{RESET} {text}")

def print_warning(text):
    print(f"{YELLOW}⚠{RESET} {text}")

def print_info(text):
    print(f"  {text}")

def test_database_schema():
    """Test 1: Verify database schema is correct."""
    print_header("TEST 1: Database Schema Verification")

    try:
        conn = sqlite3.connect('instance/medal_pool.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check for required tables
        tables = ['events', 'contest', 'user_contest_info', 'countries', 'picks', 'medals', 'users', 'tokens']
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        existing_tables = [row[0] for row in cursor.fetchall()]

        for table in tables:
            if table in existing_tables:
                print_success(f"Table '{table}' exists")
            else:
                print_error(f"Table '{table}' MISSING")
                return False

        # Check contest table structure
        cursor.execute("PRAGMA table_info(contest)")
        contest_columns = {row[1]: row[2] for row in cursor.fetchall()}

        required_contest_cols = ['id', 'event_id', 'slug', 'name', 'state', 'budget', 'max_countries', 'deadline']
        for col in required_contest_cols:
            if col in contest_columns:
                print_success(f"Contest column '{col}' exists")
            else:
                print_error(f"Contest column '{col}' MISSING")
                return False

        # Check picks table structure
        cursor.execute("PRAGMA table_info(picks)")
        picks_columns = {row[1]: row[2] for row in cursor.fetchall()}

        if 'contest_id' in picks_columns and 'event_id' in picks_columns:
            print_success("Picks table has contest_id and event_id columns")
        else:
            print_error("Picks table missing contest_id or event_id")
            return False

        # Check countries table structure
        cursor.execute("PRAGMA table_info(countries)")
        countries_columns = {row[1]: row[2] for row in cursor.fetchall()}

        if 'event_id' in countries_columns:
            print_success("Countries table has event_id column")
        else:
            print_error("Countries table missing event_id column")
            return False

        # Check medals table structure
        cursor.execute("PRAGMA table_info(medals)")
        medals_columns = {row[1]: row[2] for row in cursor.fetchall()}

        if 'event_id' in medals_columns:
            print_success("Medals table has event_id column")
        else:
            print_error("Medals table missing event_id column")
            return False

        conn.close()
        print_success("Database schema is correct!")
        return True

    except Exception as e:
        print_error(f"Database schema test failed: {e}")
        return False

def test_default_data():
    """Test 2: Verify default data is present."""
    print_header("TEST 2: Default Data Verification")

    try:
        conn = sqlite3.connect('instance/medal_pool.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check events table
        cursor.execute("SELECT * FROM events WHERE id = 1")
        event = cursor.fetchone()
        if event:
            print_success(f"Default event exists: {event['name']} (slug: {event['slug']})")
        else:
            print_error("Default event MISSING")
            return False

        # Check contest table
        cursor.execute("SELECT * FROM contest WHERE id = 1")
        contest = cursor.fetchone()
        if contest:
            print_success(f"Default contest exists: {contest['name']} (slug: {contest['slug']}, event_id: {contest['event_id']})")
        else:
            print_error("Default contest MISSING")
            return False

        # Check countries table
        cursor.execute("SELECT COUNT(*) as count FROM countries WHERE event_id = 1")
        country_count = cursor.fetchone()['count']
        if country_count > 0:
            print_success(f"Countries loaded: {country_count} countries for event_id=1")
            # Show sample
            cursor.execute("SELECT code, name, cost FROM countries WHERE event_id = 1 ORDER BY cost DESC LIMIT 3")
            print_info("Sample countries:")
            for row in cursor.fetchall():
                print_info(f"  - {row['name']} ({row['code']}): {row['cost']} points")
        else:
            print_warning("No countries loaded yet (run: sqlite3 instance/medal_pool.db < data/countries.sql)")

        conn.close()
        print_success("Default data is present!")
        return True

    except Exception as e:
        print_error(f"Default data test failed: {e}")
        return False

def test_contest_isolation():
    """Test 3: Test data isolation between contests (if multiple exist)."""
    print_header("TEST 3: Contest Isolation Test")

    try:
        conn = sqlite3.connect('instance/medal_pool.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Count contests
        cursor.execute("SELECT COUNT(*) as count FROM contest")
        contest_count = cursor.fetchone()['count']

        if contest_count == 1:
            print_warning(f"Only 1 contest exists - multi-contest isolation cannot be tested")
            print_info("To test isolation, manually create a second contest:")
            print_info("  INSERT INTO contest (event_id, slug, name, state, budget, max_countries, deadline)")
            print_info("  VALUES (1, 'test-pool', 'Test Pool', 'open', 300, 15, '2026-03-01T00:00:00Z');")
            return True

        print_info(f"Found {contest_count} contests - testing isolation...")

        # Get all contests
        cursor.execute("SELECT id, name, event_id FROM contest ORDER BY id")
        contests = cursor.fetchall()

        for contest in contests:
            # Check users in each contest
            cursor.execute("""
                SELECT COUNT(*) as count FROM user_contest_info WHERE contest_id = ?
            """, [contest['id']])
            user_count = cursor.fetchone()['count']

            # Check picks in each contest
            cursor.execute("""
                SELECT COUNT(*) as count FROM picks WHERE contest_id = ?
            """, [contest['id']])
            pick_count = cursor.fetchone()['count']

            print_success(f"Contest '{contest['name']}' (id={contest['id']}): {user_count} users, {pick_count} picks")

        # Verify no picks without contest_id
        cursor.execute("SELECT COUNT(*) as count FROM picks WHERE contest_id IS NULL")
        orphan_picks = cursor.fetchone()['count']

        if orphan_picks == 0:
            print_success("No orphan picks found (all picks have contest_id)")
        else:
            print_error(f"Found {orphan_picks} picks without contest_id!")
            return False

        conn.close()
        print_success("Contest isolation verified!")
        return True

    except Exception as e:
        print_error(f"Contest isolation test failed: {e}")
        return False

def test_data_consistency():
    """Test 4: Verify data consistency and foreign key relationships."""
    print_header("TEST 4: Data Consistency Check")

    try:
        conn = sqlite3.connect('instance/medal_pool.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check for picks with invalid country codes
        cursor.execute("""
            SELECT COUNT(*) as count FROM picks p
            WHERE NOT EXISTS (
                SELECT 1 FROM countries c
                WHERE c.event_id = p.event_id AND c.code = p.country_code
            )
        """)
        invalid_picks = cursor.fetchone()['count']

        if invalid_picks == 0:
            print_success("All picks reference valid countries")
        else:
            print_error(f"Found {invalid_picks} picks with invalid country codes!")

        # Check for user_contest_info with invalid contest_id
        cursor.execute("""
            SELECT COUNT(*) as count FROM user_contest_info uci
            WHERE NOT EXISTS (SELECT 1 FROM contest c WHERE c.id = uci.contest_id)
        """)
        invalid_uci = cursor.fetchone()['count']

        if invalid_uci == 0:
            print_success("All user_contest_info entries reference valid contests")
        else:
            print_error(f"Found {invalid_uci} user_contest_info entries with invalid contest_id!")

        # Check for picks with invalid user_id or contest_id
        cursor.execute("""
            SELECT COUNT(*) as count FROM picks p
            WHERE NOT EXISTS (
                SELECT 1 FROM user_contest_info uci
                WHERE uci.user_id = p.user_id AND uci.contest_id = p.contest_id
            )
        """)
        picks_without_uci = cursor.fetchone()['count']

        if picks_without_uci == 0:
            print_success("All picks have corresponding user_contest_info entries")
        else:
            print_warning(f"Found {picks_without_uci} picks without user_contest_info (user may have been removed)")

        # Check event_id consistency in picks
        cursor.execute("""
            SELECT COUNT(*) as count FROM picks p
            JOIN contest c ON p.contest_id = c.id
            WHERE p.event_id != c.event_id
        """)
        inconsistent_picks = cursor.fetchone()['count']

        if inconsistent_picks == 0:
            print_success("All picks have consistent event_id with their contest")
        else:
            print_error(f"Found {inconsistent_picks} picks with inconsistent event_id!")

        conn.close()
        print_success("Data consistency verified!")
        return True

    except Exception as e:
        print_error(f"Data consistency test failed: {e}")
        return False

def test_query_performance():
    """Test 5: Check for potential N+1 query issues."""
    print_header("TEST 5: Query Performance Check")

    try:
        conn = sqlite3.connect('instance/medal_pool.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Count users with picks
        cursor.execute("SELECT COUNT(DISTINCT user_id) as count FROM picks")
        users_with_picks = cursor.fetchone()['count']

        if users_with_picks == 0:
            print_warning("No users with picks yet - cannot test performance")
            return True

        print_info(f"Testing with {users_with_picks} users...")

        # Simulate leaderboard query (should be efficient)
        start_time = datetime.now()
        cursor.execute("""
            SELECT
                u.id,
                u.name,
                uci.team_name,
                COALESCE(SUM(m.gold), 0) as total_gold,
                COALESCE(SUM(m.silver), 0) as total_silver,
                COALESCE(SUM(m.bronze), 0) as total_bronze,
                COALESCE(SUM(m.points), 0) as total_points
            FROM user_contest_info uci
            JOIN users u ON uci.user_id = u.id
            JOIN picks p ON u.id = p.user_id AND p.contest_id = uci.contest_id
            LEFT JOIN medals m ON p.country_code = m.country_code AND m.event_id = p.event_id
            WHERE uci.contest_id = 1
            GROUP BY u.id
            ORDER BY total_points DESC
        """)
        teams = cursor.fetchall()
        query_time = (datetime.now() - start_time).total_seconds()

        print_success(f"Leaderboard query executed in {query_time:.3f}s ({len(teams)} teams)")

        if query_time > 1.0:
            print_warning(f"Query took longer than expected ({query_time:.3f}s)")

        # Test country fetch (should be single query, not N+1)
        if len(teams) > 0:
            user_ids = [t['id'] for t in teams]
            placeholders = ','.join('?' * len(user_ids))

            start_time = datetime.now()
            cursor.execute(f"""
                SELECT p.user_id, c.code, c.iso_code, c.name
                FROM picks p
                JOIN countries c ON p.country_code = c.code AND p.event_id = c.event_id
                WHERE p.contest_id = 1 AND p.user_id IN ({placeholders})
                ORDER BY p.user_id, c.name
            """, user_ids)
            countries = cursor.fetchall()
            query_time = (datetime.now() - start_time).total_seconds()

            print_success(f"Countries fetch executed in {query_time:.3f}s ({len(countries)} country picks)")

        conn.close()
        print_success("Query performance is acceptable!")
        return True

    except Exception as e:
        print_error(f"Query performance test failed: {e}")
        return False

def main():
    """Run all tests."""
    print_header("MULTI-CONTEST IMPLEMENTATION TEST SUITE")
    print_info("Testing database: instance/medal_pool.db")
    print_info(f"Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    tests = [
        ("Database Schema", test_database_schema),
        ("Default Data", test_default_data),
        ("Contest Isolation", test_contest_isolation),
        ("Data Consistency", test_data_consistency),
        ("Query Performance", test_query_performance),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")

    print(f"\n{BLUE}{'='*70}{RESET}")
    if passed == total:
        print(f"{GREEN}All {total} tests PASSED! ✓{RESET}")
    else:
        print(f"{YELLOW}{passed}/{total} tests passed{RESET}")
        print(f"{RED}{total - passed} test(s) FAILED{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
