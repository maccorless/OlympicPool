"""
Medal data fetching service.

Scrapes Olympic medal data from Wikipedia and updates the database.
"""

import logging
import requests
import threading
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


class MedalFetchError(Exception):
    """Raised when medal fetching fails."""
    pass


# Manual mapping for country names that don't match our database
COUNTRY_NAME_OVERRIDES = {
    "united states": "USA",
    "great britain": "GBR",
    "south korea": "KOR",
    "czech republic": "CZE",
    "roc": "ROC",  # Russian Olympic Committee
    "chinese taipei": "TPE",
    "hong kong": "HKG",
    "new zealand": "NZL",
    "south africa": "RSA",
}


def scrape_wikipedia_medals(wikipedia_url: str, timeout: int = 30) -> Tuple[List[Dict], Dict]:
    """
    Scrape medal data from Wikipedia medal table page.

    Args:
        wikipedia_url: URL to Wikipedia medal table (e.g.,
                      "https://en.wikipedia.org/wiki/2026_Winter_Olympics_medal_table")
        timeout: Request timeout in seconds

    Returns:
        Tuple of (medal_data, metadata):
        - medal_data: List of {country_name, gold, silver, bronze}
        - metadata: Dict with timestamp, source, stats

    Raises:
        MedalFetchError: If scraping fails
    """
    try:
        logger.info(f"Scraping medals from Wikipedia: {wikipedia_url}")

        # Add browser-like User-Agent to avoid 403 blocking
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        response = requests.get(wikipedia_url, headers=headers, timeout=timeout)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.content, 'lxml')

        # Find the medal table (usually has class "wikitable")
        table = soup.find('table', {'class': 'wikitable'})
        if not table:
            raise MedalFetchError("Could not find medal table on Wikipedia page")

        medal_data = []
        rows = table.find_all('tr')

        # Skip header row
        for row in rows[1:]:
            cells = row.find_all(['th', 'td'])

            # Skip if not enough columns
            if len(cells) < 4:
                continue

            # Wikipedia table has inconsistent structure for tied ranks:
            # - 6 cells: [rank] [country] [gold] [silver] [bronze] [total]
            # - 5 cells: [country] [gold] [silver] [bronze] [total] (tied rank, uses rowspan)

            # Determine if this row has a rank column
            has_rank = len(cells) == 6

            # Extract country name - position depends on whether rank is present
            country_cell = cells[1] if has_rank else cells[0]

            # Country name is in <th scope="row"> with a link
            if country_cell.name != 'th' or country_cell.get('scope') != 'row':
                # Not a country row, skip
                continue

            country_link = country_cell.find('a')
            if not country_link:
                # Try getting text directly if no link
                country_name = country_cell.get_text(strip=True)
            else:
                country_name = country_link.get_text(strip=True)

            # Remove asterisks (host country marker) and other special chars
            country_name = country_name.replace('*', '').replace('†', '').strip()

            # Skip "Totals" row
            if country_name.lower() in ('totals', 'total') or 'entries' in country_name.lower():
                continue

            # Extract medal counts - position depends on whether rank is present
            gold_idx = 2 if has_rank else 1
            silver_idx = 3 if has_rank else 2
            bronze_idx = 4 if has_rank else 3

            try:
                gold = int(cells[gold_idx].get_text(strip=True) or 0)
                silver = int(cells[silver_idx].get_text(strip=True) or 0)
                bronze = int(cells[bronze_idx].get_text(strip=True) or 0)
            except (ValueError, IndexError) as e:
                logger.warning(f"Could not parse medal counts for {country_name}: {e}, skipping")
                continue

            # Only include countries with at least one medal
            if gold > 0 or silver > 0 or bronze > 0:
                medal_data.append({
                    'country_name': country_name,
                    'gold': gold,
                    'silver': silver,
                    'bronze': bronze
                })

        metadata = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source': 'wikipedia',
            'countries_fetched': len(medal_data)
        }

        logger.info(f"Successfully scraped medals for {len(medal_data)} countries from Wikipedia")
        return medal_data, metadata

    except requests.RequestException as e:
        raise MedalFetchError(f"HTTP request failed: {e}")
    except Exception as e:
        raise MedalFetchError(f"Failed to parse Wikipedia page: {e}")


def map_country_name_to_code(country_name: str, db, event_id: int) -> Optional[str]:
    """
    Map Wikipedia country name to IOC code in database.

    Tries multiple strategies:
    1. Manual override mapping (for known edge cases)
    2. Direct match on countries.name (case-insensitive)
    3. Partial match (handles cases like "United States" vs "United States of America")

    Args:
        country_name: Country name from Wikipedia
        db: Database connection
        event_id: Event ID to search within

    Returns:
        country_code (IOC code) or None if no match
    """
    # Normalize name
    normalized_name = country_name.lower().strip()

    # Check manual overrides first
    if normalized_name in COUNTRY_NAME_OVERRIDES:
        code = COUNTRY_NAME_OVERRIDES[normalized_name]
        logger.debug(f"Mapped '{country_name}' to '{code}' via override")
        return code

    # Try exact match
    result = db.execute('''
        SELECT code FROM countries
        WHERE event_id = ? AND LOWER(name) = ?
    ''', [event_id, normalized_name]).fetchone()

    if result:
        logger.debug(f"Mapped '{country_name}' to '{result['code']}' via exact match")
        return result['code']

    # Try partial match (first word)
    # E.g., "United States" matches "United States of America"
    first_word = normalized_name.split()[0] if ' ' in normalized_name else normalized_name
    result = db.execute('''
        SELECT code FROM countries
        WHERE event_id = ? AND LOWER(name) LIKE ?
    ''', [event_id, f"{first_word}%"]).fetchone()

    if result:
        logger.debug(f"Mapped '{country_name}' to '{result['code']}' via partial match")
        return result['code']

    # No match found
    logger.warning(f"Could not map country name '{country_name}' to database code")
    return None


def update_medals_in_database(db, event_id: int, medal_data: List[Dict]) -> Tuple[int, List[str], bool]:
    """
    Update medals table with fetched data.

    Args:
        db: Database connection
        event_id: Event ID to update medals for
        medal_data: List of dicts with:
                    {country_name, gold, silver, bronze} (Wikipedia format)

    Returns:
        Tuple of (updated_count, unmatched_countries, data_changed)
        - updated_count: Number of countries updated
        - unmatched_countries: List of countries that couldn't be mapped
        - data_changed: True if any medal counts actually changed
    """
    updated_count = 0
    unmatched_countries = []
    data_changed = False

    try:
        db.execute('BEGIN')

        for entry in medal_data:
            # Map country name to code
            country_code = map_country_name_to_code(entry['country_name'], db, event_id)
            if not country_code:
                unmatched_countries.append(entry['country_name'])
                logger.warning(f"Could not map country name to code: {entry['country_name']}")
                continue

            # Verify country exists in our database
            country = db.execute('''
                SELECT code FROM countries
                WHERE event_id = ? AND code = ?
            ''', [event_id, country_code]).fetchone()

            if not country:
                display_name = entry.get('country_name', country_code)
                unmatched_countries.append(f"{display_name} ({country_code})")
                logger.warning(f"Country not found in database: {country_code}")
                continue

            # Calculate points
            gold = entry['gold']
            silver = entry['silver']
            bronze = entry['bronze']
            points = gold * 3 + silver * 2 + bronze

            # Check if data actually changed
            existing = db.execute('''
                SELECT gold, silver, bronze FROM medals
                WHERE event_id = ? AND country_code = ?
            ''', [event_id, country_code]).fetchone()

            if existing:
                # Compare with existing data
                if (existing['gold'] != gold or
                    existing['silver'] != silver or
                    existing['bronze'] != bronze):
                    data_changed = True
                    logger.info(f"Medal data changed for {country_code}: {existing['gold']}/{existing['silver']}/{existing['bronze']} → {gold}/{silver}/{bronze}")
            else:
                # New country with medals - this is a change
                if gold > 0 or silver > 0 or bronze > 0:
                    data_changed = True
                    logger.info(f"New medals for {country_code}: {gold}/{silver}/{bronze}")

            # Update or insert medal data
            db.execute('''
                INSERT INTO medals (event_id, country_code, gold, silver, bronze, points, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(event_id, country_code) DO UPDATE SET
                    gold = excluded.gold,
                    silver = excluded.silver,
                    bronze = excluded.bronze,
                    points = excluded.points,
                    updated_at = excluded.updated_at
            ''', [
                event_id,
                country_code,
                gold,
                silver,
                bronze,
                points,
                datetime.now(timezone.utc).isoformat()
            ])

            updated_count += 1

        db.commit()
        logger.info(f"Updated medals for {updated_count} countries, data_changed={data_changed}")

        return updated_count, unmatched_countries, data_changed

    except Exception as e:
        db.rollback()
        logger.error(f"Database update failed: {e}")
        raise


def scrape_wikipedia_and_update_medals(db, event_id: int, wikipedia_url: str) -> Dict:
    """
    Scrape medals from Wikipedia and update database (complete workflow).

    Args:
        db: Database connection
        event_id: Event ID to update
        wikipedia_url: Wikipedia medal table URL

    Returns:
        Dict with operation results and metadata
    """
    try:
        # Scrape medal data
        medal_data, metadata = scrape_wikipedia_medals(wikipedia_url)

        # Update database
        updated_count, unmatched_countries, data_changed = update_medals_in_database(db, event_id, medal_data)

        # Store metadata in system_meta
        meta_key = f'medals_last_scrape_{event_id}'
        meta_value = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source': metadata['source'],
            'success': True,
            'countries_fetched': metadata['countries_fetched'],
            'countries_updated': updated_count,
            'unmatched_countries': unmatched_countries,
            'data_changed': data_changed
        }

        import json
        db.execute('''
            INSERT INTO system_meta (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
        ''', [meta_key, json.dumps(meta_value)])
        db.commit()

        return {
            'success': True,
            'updated_count': updated_count,
            'unmatched_countries': unmatched_countries,
            'data_changed': data_changed,
            'metadata': metadata
        }

    except MedalFetchError as e:
        logger.error(f"Wikipedia scrape failed: {e}")

        # Store error in system_meta
        meta_key = f'medals_last_scrape_{event_id}'
        meta_value = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source': 'wikipedia',
            'success': False,
            'error': str(e)
        }

        import json
        db.execute('''
            INSERT INTO system_meta (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
        ''', [meta_key, json.dumps(meta_value)])
        db.commit()

        return {
            'success': False,
            'error': str(e)
        }


def get_last_scrape_metadata(db, event_id: int) -> Optional[Dict]:
    """
    Get metadata from last medal scrape operation.

    Args:
        db: Database connection
        event_id: Event ID

    Returns:
        Dict with last scrape metadata, or None if never scraped
    """
    meta_key = f'medals_last_scrape_{event_id}'
    row = db.execute('''
        SELECT value FROM system_meta WHERE key = ?
    ''', [meta_key]).fetchone()

    if not row:
        return None

    import json
    return json.loads(row['value'])


def is_medal_data_stale(db, event_id: int, staleness_seconds: int = 900) -> Tuple[bool, Optional[datetime]]:
    """
    Check if medal data is stale (needs refresh).

    Args:
        db: Database connection
        event_id: Event ID to check
        staleness_seconds: Consider stale if older than this many seconds (default: 900 = 15 minutes)

    Returns:
        Tuple of (is_stale, last_updated_datetime)
        - is_stale: True if data is older than staleness_seconds
        - last_updated_datetime: When medals were last updated (None if never updated)
    """
    # Get last update timestamp from medals table
    result = db.execute('''
        SELECT MAX(updated_at) as last_updated
        FROM medals
        WHERE event_id = ?
    ''', [event_id]).fetchone()

    if not result or not result['last_updated']:
        # No medal data exists - definitely stale
        return True, None

    # Parse ISO8601 timestamp
    last_updated_str = result['last_updated']

    # Handle different timestamp formats from SQLite
    if last_updated_str.endswith('Z'):
        last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
    elif '+' in last_updated_str or last_updated_str.count(':') > 2:
        # Already has timezone info
        last_updated = datetime.fromisoformat(last_updated_str)
    else:
        # Naive datetime from SQLite - assume UTC
        last_updated = datetime.fromisoformat(last_updated_str).replace(tzinfo=timezone.utc)

    # Calculate time difference
    now = datetime.now(timezone.utc)
    seconds_since_update = (now - last_updated).total_seconds()

    is_stale = seconds_since_update > staleness_seconds

    return is_stale, last_updated


def trigger_background_medal_scrape(app, event_id: int, wikipedia_url: str):
    """
    Trigger medal scrape in background thread (non-blocking).

    Args:
        app: Flask application instance
        event_id: Event ID to update
        wikipedia_url: Wikipedia URL to scrape

    Note: Creates new database connection inside thread to avoid sharing connections across threads.
    """
    def scrape_task():
        try:
            # Import db getter inside thread
            from app.db import get_db

            # Push application context for this thread
            with app.app_context():
                # Check scrape lock to prevent concurrent scrapes
                db = get_db()
                scrape_lock_key = f'medal_scrape_in_progress_{event_id}'
                scrape_lock = db.execute('''
                    SELECT value FROM system_meta WHERE key = ?
                ''', [scrape_lock_key]).fetchone()

                if scrape_lock and scrape_lock['value'] == 'true':
                    logger.info(f"Scrape already in progress for event {event_id}, skipping")
                    return

                # Set lock
                db.execute('''
                    INSERT INTO system_meta (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(key) DO UPDATE SET
                        value = excluded.value,
                        updated_at = CURRENT_TIMESTAMP
                ''', [scrape_lock_key, 'true'])
                db.commit()

                try:
                    # Perform scrape
                    scrape_wikipedia_and_update_medals(db, event_id, wikipedia_url)
                    logger.info(f"Background medal scrape completed for event {event_id}")
                except Exception as scrape_error:
                    logger.error(f"Scrape error for event {event_id}: {scrape_error}")
                finally:
                    # Clear lock (always, even on error)
                    db.execute('''
                        UPDATE system_meta SET value = 'false' WHERE key = ?
                    ''', [scrape_lock_key])
                    db.commit()

        except Exception as e:
            logger.error(f"Background thread failed for event {event_id}: {e}")

    # Start scrape in background thread
    logger.info(f"Triggering background medal scrape for event {event_id}")
    thread = threading.Thread(target=scrape_task, daemon=True)
    thread.start()


def format_timestamp_cet(utc_timestamp_str: Optional[str]) -> Optional[str]:
    """
    Convert UTC ISO8601 timestamp to CET/CEST human-readable format.

    Args:
        utc_timestamp_str: ISO8601 UTC timestamp string

    Returns:
        Formatted string like "Feb 8, 2026 3:45 PM CET" or None
    """
    if not utc_timestamp_str:
        return None

    try:
        # Parse UTC timestamp
        if utc_timestamp_str.endswith('Z'):
            utc_time = datetime.fromisoformat(utc_timestamp_str.replace('Z', '+00:00'))
        elif '+' in utc_timestamp_str or utc_timestamp_str.count(':') > 2:
            # Already has timezone info
            utc_time = datetime.fromisoformat(utc_timestamp_str)
        else:
            # Naive datetime - assume UTC
            utc_time = datetime.fromisoformat(utc_timestamp_str).replace(tzinfo=timezone.utc)

        # Convert to Europe/Rome timezone (handles CET/CEST automatically)
        milan_tz = ZoneInfo('Europe/Rome')
        milan_time = utc_time.astimezone(milan_tz)

        # Format: "Feb 8, 2026 3:45 PM CET"
        # Note: %-d and %-I are Unix format codes (no padding), %#d and %#I for Windows
        try:
            formatted = milan_time.strftime('%b %-d, %Y %-I:%M %p %Z')
        except ValueError:
            # Windows doesn't support -, try # instead
            formatted = milan_time.strftime('%b %#d, %Y %#I:%M %p %Z')

        return formatted
    except Exception as e:
        logger.warning(f"Failed to convert timestamp to CET: {e}")
        return utc_timestamp_str  # Fallback to original
