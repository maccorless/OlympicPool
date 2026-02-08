# Removed Olympics.com API Scraping

## Summary

Removed all Olympics.com API scraping functionality per user request. The app now uses **only Wikipedia scraping** for automatic medal updates, which is simpler and more reliable.

## What Was Removed

### 1. **Service Functions** (`app/services/medal_fetcher.py`)

Removed:
- `fetch_medals_from_json_api()` - Fetched medal data from Olympics.com JSON API
- `scrape_and_update_medals()` - Wrapper function for Olympics.com workflow

**Before:** 545 lines
**After:** 370 lines
**Lines removed:** ~175

### 2. **Admin Route** (`app/routes/admin.py`)

Removed:
- `POST /<event_slug>/<contest_slug>/admin/medals/scrape` - Olympics.com scrape endpoint

Simplified:
- `admin_medals()` - Removed `olympics_api_configured` variable
- `admin_dashboard()` - Removed `olympics_api_configured` variable

### 3. **Template** (`app/templates/admin/medals.html`)

Removed:
- "🏅 Refresh from Olympics.com" button
- Dual-source UI logic
- Olympics.com specific status display

Simplified:
- Now shows single "📚 Refresh from Wikipedia" button
- Cleaner status display focused on Wikipedia scraping

### 4. **Database Schema** (No changes needed)

**Note:** The `olympics_api_slug` column in the `events` table still exists but is now unused. We kept it to avoid migration complexity, but it can be removed in a future cleanup if desired.

## What Remains

### ✅ Wikipedia Scraping (Only medal update method)

**Service:** `app/services/medal_fetcher.py`
- `scrape_wikipedia_medals()` - Scrapes Wikipedia medal table
- `map_country_name_to_code()` - Maps country names to IOC codes
- `update_medals_in_database()` - Updates medals table
- `scrape_wikipedia_and_update_medals()` - Complete workflow
- `get_last_scrape_metadata()` - Retrieves last scrape status

**Route:** `POST /<event_slug>/<contest_slug>/admin/medals/scrape-wikipedia`

**Template:** Single "Refresh from Wikipedia" button

### ✅ Manual Entry Methods (Unchanged)

1. **Individual Entry** - Type medals directly into form
2. **Bulk Paste** - Paste from Excel/spreadsheet

## Configuration

### Wikipedia URL (Required for Auto-Scraping)

Set `wikipedia_medal_url` in the `events` table:

```sql
UPDATE events
SET wikipedia_medal_url = 'https://en.wikipedia.org/wiki/2026_Winter_Olympics_medal_table'
WHERE slug = 'mc26';
```

### Olympics API Slug (Now Unused)

The `olympics_api_slug` column still exists but is no longer used:

```sql
-- This column is ignored now
SELECT olympics_api_slug FROM events;
```

You can set it to NULL if desired:

```sql
UPDATE events SET olympics_api_slug = NULL;
```

## Testing

### Verify Wikipedia Scraping Still Works

```bash
source .venv/bin/activate
python test_wikipedia_scraper.py
```

Expected output:
```
✓ Successfully scraped 29 countries
Source: wikipedia
```

### Verify Admin UI

1. Navigate to `/mc26/test/admin/medals`
2. Should see **only one button**: "📚 Refresh from Wikipedia"
3. No Olympics.com button should appear
4. Status should show "Source: wikipedia" after scraping

## Rationale for Removal

Per user feedback:
> "the olympics.com scrape should be fully removed. we decided it was too complex with playwright, etc."

**Benefits of removal:**
- ✅ Simpler codebase (175 fewer lines)
- ✅ Single source of truth for medal data
- ✅ No dependency on Olympics.com API structure
- ✅ Wikipedia is more reliable during high-traffic Olympics
- ✅ No need to configure `olympics_api_slug`
- ✅ Cleaner admin UI (one button vs two)

## Migration Notes

### If You Had Olympics.com API Configured

No action needed! The app will work fine. The `olympics_api_slug` column is simply ignored now.

If you want to clean up:

```sql
-- Optional: Clear unused Olympics API slugs
UPDATE events SET olympics_api_slug = NULL;
```

### If You Had Scrape Metadata from Olympics.com

Old scrape metadata in `system_meta` will still display correctly. The next Wikipedia scrape will update it with `source: wikipedia`.

## File Comparison

### Before (Dual-Source)

```
app/services/medal_fetcher.py (545 lines)
├── fetch_medals_from_json_api()         ← REMOVED
├── scrape_wikipedia_medals()
├── map_country_name_to_code()
├── update_medals_in_database()
├── scrape_and_update_medals()           ← REMOVED (Olympics.com workflow)
├── scrape_wikipedia_and_update_medals()
└── get_last_scrape_metadata()

app/routes/admin.py
├── admin_medals_scrape()                ← REMOVED (Olympics.com route)
└── admin_medals_scrape_wikipedia()

app/templates/admin/medals.html
├── Olympics.com button                  ← REMOVED
└── Wikipedia button
```

### After (Wikipedia-Only)

```
app/services/medal_fetcher.py (370 lines)
├── scrape_wikipedia_medals()
├── map_country_name_to_code()
├── update_medals_in_database()
├── scrape_wikipedia_and_update_medals()
└── get_last_scrape_metadata()

app/routes/admin.py
└── admin_medals_scrape_wikipedia()

app/templates/admin/medals.html
└── Wikipedia button (only)
```

## Code Quality

### Syntax Validation

All modified files validated:
- ✅ `app/services/medal_fetcher.py` - Compiles without errors
- ✅ `app/routes/admin.py` - Compiles without errors
- ✅ `app/templates/admin/medals.html` - Jinja2 valid

### Functional Testing

- ✅ Wikipedia scraper tested with live data (2022 Winter Olympics)
- ✅ Successfully scraped 29 countries
- ✅ Country name mapping working correctly
- ✅ Medal count extraction accurate

## Future Considerations

### Optional: Remove olympics_api_slug Column

If you want to fully clean up the database schema:

```sql
-- Create migration: migrations/remove_olympics_api_slug.sql
ALTER TABLE events DROP COLUMN olympics_api_slug;
```

**Note:** This is optional and cosmetic. The column being present doesn't cause any issues.

### Optional: Update Documentation

Update these files to reflect Wikipedia-only approach:
- `CLAUDE.md` - Update medal data sources section
- `README.md` - Update features list
- `WIKIPEDIA_SCRAPING.md` - Remove Olympics.com comparison table

## Summary

**Result:** Cleaner, simpler codebase with single reliable medal data source (Wikipedia).

**No breaking changes:** Existing functionality preserved, only Olympics.com scraping removed.

**Testing:** All tests pass, Wikipedia scraping working correctly.
