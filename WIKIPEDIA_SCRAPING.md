# Wikipedia Medal Scraping

This document explains the Wikipedia medal scraping feature for the Olympic Medal Pool application.

## Overview

The application uses Wikipedia medal tables as the source for automatic medal updates. Wikipedia provides:

- **Reliability**: Stable during high-traffic Olympics periods (no rate-limiting)
- **No Authentication**: Public data, no API keys required
- **Community Curated**: Errors caught quickly by Wikipedia editors
- **Stable Format**: Medal table structure rarely changes

## How It Works

### Wikipedia Medal Table Structure

Wikipedia medal tables follow a consistent format:
- URL pattern: `https://en.wikipedia.org/wiki/{Year}_{Season}_Olympics_medal_table`
- Table class: `wikitable`
- Columns: Rank, NOC (country), Gold, Silver, Bronze, Total

Example for 2026 Winter Olympics:
```
https://en.wikipedia.org/wiki/2026_Winter_Olympics_medal_table
```

### Scraping Process

1. Admin clicks "📚 Refresh from Wikipedia" button
2. Backend fetches HTML from Wikipedia URL
3. BeautifulSoup parses the medal table
4. Country names are mapped to IOC codes in database
5. Medal counts are updated in the `medals` table
6. Metadata stored in `system_meta` for audit trail

### Country Name Mapping

Wikipedia uses full country names (e.g., "United States", "Great Britain"), while our database uses IOC codes (e.g., "USA", "GBR").

**Mapping Strategy:**

1. **Manual overrides** - Hardcoded mappings for edge cases:
   ```python
   COUNTRY_NAME_OVERRIDES = {
       "united states": "USA",
       "great britain": "GBR",
       "south korea": "KOR",
       # ... etc
   }
   ```

2. **Exact match** - Case-insensitive match on `countries.name`

3. **Partial match** - First word match (handles "United States" vs "United States of America")

If no match is found, the country is skipped and listed in warnings.

## Configuration

### Setting Wikipedia URL for an Event

Add the Wikipedia URL to the `events` table:

```sql
UPDATE events
SET wikipedia_medal_url = 'https://en.wikipedia.org/wiki/2026_Winter_Olympics_medal_table'
WHERE slug = 'milano-2026';
```

### Migration for Existing Databases

Run the migration to add the column (if not already done):

```bash
sqlite3 instance/medal_pool.db < migrations/add_wikipedia_medal_url.sql
```

## Admin Interface

### Medal Entry Page

When `wikipedia_medal_url` is configured for an event, admins see a single "📚 Refresh from Wikipedia" button in the Auto-Refresh section.

### Scrape Status

After scraping, the admin sees:

- **Timestamp** - When medals were last updated
- **Status** - Success/failure
- **Countries Updated** - How many countries had medal data updated
- **Warnings** - Countries that couldn't be matched to database

## Testing

### Test the Wikipedia Scraper

Run the test script to verify Wikipedia scraping works:

```bash
source .venv/bin/activate
python test_wikipedia_scraper.py
```

This tests scraping from the 2022 Winter Olympics Wikipedia page (complete data) and the 2026 page (current data).

### Manual Testing

1. Set up an event with Wikipedia URL:
   ```sql
   UPDATE events
   SET wikipedia_medal_url = 'https://en.wikipedia.org/wiki/2022_Winter_Olympics_medal_table'
   WHERE id = 1;
   ```

2. Navigate to `/milano-2026/office-pool/admin/medals`

3. Click "📚 Refresh from Wikipedia" button

4. Verify medal counts are updated

5. Check for any unmatched country warnings

## Adding Country Name Overrides

If Wikipedia uses a country name that doesn't match your database, add it to `COUNTRY_NAME_OVERRIDES` in `app/services/medal_fetcher.py`:

```python
COUNTRY_NAME_OVERRIDES = {
    "united states": "USA",
    "great britain": "GBR",
    "south korea": "KOR",
    "your new mapping": "IOC",  # Add here
}
```

## Technical Details

### Dependencies

- `beautifulsoup4>=4.12.0` - HTML parsing
- `lxml>=4.9.0` - Fast XML/HTML parser

### Key Files

- `app/services/medal_fetcher.py` - Scraping logic
  - `scrape_wikipedia_medals()` - Fetch and parse Wikipedia table
  - `map_country_name_to_code()` - Map country names to IOC codes
  - `scrape_wikipedia_and_update_medals()` - Complete workflow

- `app/routes/admin.py`
  - `admin_medals_scrape_wikipedia()` - Admin route for Wikipedia scraping

- `app/templates/admin/medals.html` - Admin UI with Wikipedia refresh button

- `schema.sql` - Added `wikipedia_medal_url` column to `events` table

### Error Handling

The scraper handles:

- **HTTP errors** - Network issues, 404s, timeouts
- **Parsing errors** - Invalid HTML structure
- **Unmapped countries** - Countries not in database
- **Empty tables** - No medal data yet (early in Games)
- **Tied ranks** - Wikipedia uses rowspan for tied countries

All errors are logged and displayed to admin with friendly messages.

## Medal Update Methods

The application supports three methods for updating medals:

| Method | Trigger | Use Case |
|--------|---------|----------|
| **Wikipedia Scraping** | Admin clicks button | Quick updates during Games (recommended) |
| **Bulk Paste** | Admin pastes TSV data | Import full standings from Excel |
| **Individual Entry** | Admin types manually | Spot corrections |

**Recommendation:** Use Wikipedia scraping for regular updates, as it's the fastest and most reliable method.

## Metadata Tracking

Every scrape stores metadata in `system_meta` table:

```json
{
  "timestamp": "2026-02-08T12:34:56Z",
  "source": "wikipedia",
  "success": true,
  "countries_fetched": 8,
  "countries_updated": 8,
  "unmatched_countries": []
}
```

**Key:** `medals_last_scrape_{event_id}`

This is displayed on:
- Admin dashboard: Medal data status card
- Medal entry page: Auto-refresh section

## Handling Tied Ranks

Wikipedia uses `rowspan` for tied countries. Example:

```html
<!-- Rank 1: Italy (has rowspan) -->
<tr>
  <td>1</td>
  <th scope="row"><a>Italy</a></th>
  <td>1</td><td>1</td><td>1</td><td>3</td>
</tr>

<!-- Rank 1: Japan (no rank cell, shares rowspan) -->
<tr>
  <th scope="row"><a>Japan</a></th>
  <td>1</td><td>1</td><td>1</td><td>3</td>
</tr>
```

The scraper detects both patterns:
- **6 cells**: `[rank] [country] [gold] [silver] [bronze] [total]`
- **5 cells**: `[country] [gold] [silver] [bronze] [total]` (tied rank)

This ensures all countries are captured correctly, even when tied.

## Troubleshooting

### "Wikipedia URL not configured"

The event needs `wikipedia_medal_url` set in the database:

```sql
UPDATE events
SET wikipedia_medal_url = 'https://en.wikipedia.org/wiki/2026_Winter_Olympics_medal_table'
WHERE slug = 'your-event-slug';
```

### Countries Not Matching

Add overrides to `COUNTRY_NAME_OVERRIDES` in `app/services/medal_fetcher.py` for any countries that don't map automatically.

### HTTP 403 Errors

The scraper uses a browser-like User-Agent. If you still get 403 errors, Wikipedia or your network may be blocking the request. Try from a different network.

### No Data Scraped

Early in the Games, Wikipedia tables may not have data yet. The scraper will return 0 countries, which is expected. Wait until events have finished and medals are awarded.

## Future Enhancements

Potential improvements:

1. **Scheduled scraping** - Cron job to auto-refresh during Games
2. **Diff tracking** - Show which medals changed since last scrape
3. **Historical data** - Archive medal counts for each scrape
4. **Country mapping UI** - Admin interface to add/edit country name mappings
5. **Validation alerts** - Flag unusual changes (e.g., medal count decreased)

## See Also

- `SETUP_WIKIPEDIA_SCRAPING.md` - Step-by-step setup guide
- `REMOVED_OLYMPICS_API.md` - Why Olympics.com API was removed
- `test_wikipedia_scraper.py` - Test script for validation
