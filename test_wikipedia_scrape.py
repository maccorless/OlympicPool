#!/usr/bin/env python3
"""Smoke test for Wikipedia medal scraping."""
import sys
from app.services.medal_fetcher import scrape_wikipedia_medals

def main():
    url = 'https://en.wikipedia.org/wiki/2026_Winter_Olympics_medal_table'
    print(f"Testing Wikipedia scrape from: {url}")
    print("-" * 60)

    try:
        medal_data, metadata = scrape_wikipedia_medals(url)
        print(f"✅ Success! Countries fetched: {metadata['countries_fetched']}")

        if medal_data:
            print("\nSample countries (first 5):")
            for country in medal_data[:5]:
                print(f"  {country['country_name']}: {country['gold']}G / {country['silver']}S / {country['bronze']}B")
        else:
            print("⚠️  No medal data found (Games may not have started yet)")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
