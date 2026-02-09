#!/usr/bin/env python3
"""Full test of Wikipedia medal scraping with verification."""
import sys
import sqlite3
from app import create_app
from app.db import get_db
from app.services.medal_fetcher import scrape_wikipedia_and_update_medals

def main():
    print("=" * 70)
    print("WIKIPEDIA MEDAL SCRAPER TEST")
    print("=" * 70)

    # Create Flask app context
    app = create_app()

    with app.app_context():
        db = get_db()

        # Get Wikipedia URL from contest
        contest = db.execute('SELECT wikipedia_medal_url FROM contest WHERE id = 1').fetchone()
        wikipedia_url = contest['wikipedia_medal_url']

        print(f"\n📚 Wikipedia URL: {wikipedia_url}")

        # Check medals before scrape
        before = db.execute('''
            SELECT
                SUM(gold) as total_gold,
                SUM(silver) as total_silver,
                SUM(bronze) as total_bronze,
                SUM(gold) + SUM(silver) + SUM(bronze) as total_medals
            FROM medals
        ''').fetchone()

        print(f"\n📊 BEFORE SCRAPE:")
        print(f"   Gold: {before['total_gold'] or 0}")
        print(f"   Silver: {before['total_silver'] or 0}")
        print(f"   Bronze: {before['total_bronze'] or 0}")
        print(f"   Total medals: {before['total_medals'] or 0}")

        # Run the scrape
        print(f"\n🔄 Running Wikipedia scrape...")
        result = scrape_wikipedia_and_update_medals(db, wikipedia_url)

        if result['success']:
            print(f"\n✅ SCRAPE SUCCESSFUL!")
            print(f"   Countries updated: {result['updated_count']}")

            if result.get('unmatched_countries'):
                print(f"   ⚠️  Unmatched countries: {', '.join(result['unmatched_countries'][:5])}")

            # Check medals after scrape
            after = db.execute('''
                SELECT
                    SUM(gold) as total_gold,
                    SUM(silver) as total_silver,
                    SUM(bronze) as total_bronze,
                    SUM(gold) + SUM(silver) + SUM(bronze) as total_medals
                FROM medals
            ''').fetchone()

            print(f"\n📊 AFTER SCRAPE:")
            print(f"   Gold: {after['total_gold']}")
            print(f"   Silver: {after['total_silver']}")
            print(f"   Bronze: {after['total_bronze']}")
            print(f"   Total medals: {after['total_medals']}")

            # Verify expected total
            expected_total = 33
            if after['total_medals'] == expected_total:
                print(f"\n🎯 VERIFICATION PASSED! Total medals = {expected_total} ✅")
            else:
                print(f"\n⚠️  VERIFICATION MISMATCH!")
                print(f"   Expected: {expected_total}")
                print(f"   Actual: {after['total_medals']}")
                print(f"   Difference: {after['total_medals'] - expected_total}")

            # Show top 10 countries
            print(f"\n🏆 TOP 10 COUNTRIES:")
            countries = db.execute('''
                SELECT c.name, m.gold, m.silver, m.bronze, m.points
                FROM medals m
                JOIN countries c ON m.country_code = c.code
                ORDER BY m.points DESC
                LIMIT 10
            ''').fetchall()

            for i, country in enumerate(countries, 1):
                print(f"   {i}. {country['name']:<20} {country['gold']}G / {country['silver']}S / {country['bronze']}B (Points: {country['points']})")

        else:
            print(f"\n❌ SCRAPE FAILED!")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            sys.exit(1)

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == '__main__':
    main()
