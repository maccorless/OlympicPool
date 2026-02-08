#!/usr/bin/env python3
"""
Test script for Wikipedia medal scraping.
Run this to verify Wikipedia scraping works correctly.
"""

import sys
from app.services.medal_fetcher import scrape_wikipedia_medals, MedalFetchError

def test_wikipedia_scraper():
    """Test Wikipedia scraping with 2026 Winter Olympics medal table."""

    # Use 2026 Winter Olympics Wikipedia page (note: this may not have data yet)
    # For testing, we can use a past Olympics that has complete data
    test_urls = [
        ("2022 Winter", "https://en.wikipedia.org/wiki/2022_Winter_Olympics_medal_table"),
        ("2026 Winter", "https://en.wikipedia.org/wiki/2026_Winter_Olympics_medal_table"),
    ]

    print("Testing Wikipedia Medal Scraper")
    print("=" * 60)

    for name, url in test_urls:
        print(f"\nTesting {name} Olympics: {url}")
        print("-" * 60)

        try:
            medal_data, metadata = scrape_wikipedia_medals(url, timeout=15)

            print(f"✓ Successfully scraped {metadata['countries_fetched']} countries")
            print(f"Source: {metadata['source']}")
            print(f"\nFirst 10 countries:")
            print(f"{'Country':<30} {'Gold':<6} {'Silver':<6} {'Bronze':<6}")
            print("-" * 60)

            for country in medal_data[:10]:
                print(f"{country['country_name']:<30} {country['gold']:<6} {country['silver']:<6} {country['bronze']:<6}")

            if metadata['countries_fetched'] > 10:
                print(f"\n... and {metadata['countries_fetched'] - 10} more countries")

            print("\n✓ Wikipedia scraping successful!")
            return True

        except MedalFetchError as e:
            print(f"✗ Failed to scrape Wikipedia: {e}")
            continue

    print("\n✗ All test URLs failed")
    return False


if __name__ == '__main__':
    success = test_wikipedia_scraper()
    sys.exit(0 if success else 1)
