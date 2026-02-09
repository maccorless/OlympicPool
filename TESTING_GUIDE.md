# Wikipedia Auto-Scraping Testing Guide

Flask is running at: **http://127.0.0.1:5001**

## Current Configuration

✅ Contest state: **locked** (auto-refresh enabled)
✅ Staleness threshold: **10 seconds** (for easy testing)
✅ Wikipedia URL: https://en.wikipedia.org/wiki/2026_Winter_Olympics_medal_table
✅ Admin email: ken@corless.com

---

## Test 1: Admin Panel - Manual Wikipedia Refresh

### Steps:

1. **Login as Admin**
   - Go to: http://127.0.0.1:5001/login
   - Enter phone number (your registered number)
   - Enter the OTP code (shown on page since NO_SMS_MODE=False)

2. **Navigate to Medal Entry**
   - Go to: http://127.0.0.1:5001/admin/medals

3. **Verify Wikipedia Section Appears**
   You should see a blue box at the top with:
   ```
   🔄 Auto-Refresh from Wikipedia

   Last updated: [timestamp] UTC
   Status: ✓ Success - 15 countries updated

   [📚 Refresh from Wikipedia] button
   ```

4. **Click the Refresh Button**
   - Click "📚 Refresh from Wikipedia"
   - Should redirect back with success message
   - Medal counts should update in the table below

5. **Verify Success Message**
   Should see: "Successfully updated medal counts for 15 countries from Wikipedia!"

---

## Test 2: Leaderboard Auto-Refresh (10-Second Staleness)

### Steps:

1. **Note Current Medal Data**
   ```bash
   cd /Users/kcorless/Documents/Projects/OlympicPool
   sqlite3 instance/medal_pool.db "SELECT updated_at FROM medals LIMIT 1;"
   ```

2. **Visit Leaderboard**
   - Go to: http://127.0.0.1:5001/leaderboard
   - This first visit should NOT trigger a scrape (data is fresh)

3. **Wait 10+ Seconds**
   - Medal data will be considered "stale" after 10 seconds

4. **Visit Leaderboard Again**
   - Refresh the page or visit again
   - Check Flask logs for: "Triggered background Wikipedia scrape (data stale)"

5. **Monitor Flask Logs**
   ```bash
   cd /Users/kcorless/Documents/Projects/OlympicPool
   tail -f flask.log
   ```

   You should see:
   ```
   INFO in leaderboard: Triggered background Wikipedia scrape (data stale)
   INFO in medal_fetcher: Scraping medals from Wikipedia: https://...
   INFO in medal_fetcher: Successfully scraped medals for 15 countries from Wikipedia
   INFO in medal_fetcher: Background medal scrape completed
   ```

6. **Verify Auto-Update Worked**
   ```bash
   sqlite3 instance/medal_pool.db "SELECT COUNT(*) || ' countries updated' FROM medals WHERE updated_at > datetime('now', '-30 seconds');"
   ```
   Should show 15 countries with recent timestamps.

---

## Test 3: Verify Scrape Metadata

Check the system metadata table for scrape results:

```bash
cd /Users/kcorless/Documents/Projects/OlympicPool
sqlite3 instance/medal_pool.db "SELECT value FROM system_meta WHERE key = 'medals_last_scrape';" | python -m json.tool
```

Should show:
```json
{
  "timestamp": "2026-02-08T...",
  "source": "wikipedia",
  "success": true,
  "countries_fetched": 15,
  "countries_updated": 15,
  "unmatched_countries": [],
  "data_changed": true
}
```

---

## Test 4: Verify Country Name Mapping

The scraper should correctly map Wikipedia country names to database codes:

```bash
cd /Users/kcorless/Documents/Projects/OlympicPool
sqlite3 instance/medal_pool.db "SELECT c.name, c.code, m.gold, m.silver, m.bronze FROM medals m JOIN countries c ON m.country_code = c.code WHERE m.points > 0 ORDER BY m.points DESC LIMIT 10;"
```

---

## Test 5: Leaderboard Display

Visit: http://127.0.0.1:5001/leaderboard

**Should show:**
- ✅ All teams ranked by points
- ✅ Medal counts for each team
- ✅ Country flags for picked countries
- ✅ Correct point calculations (gold×3 + silver×2 + bronze×1)

---

## Quick Verification Commands

```bash
# Check current medal totals
sqlite3 instance/medal_pool.db "SELECT SUM(gold) + SUM(silver) + SUM(bronze) as total FROM medals;"
# Should show: 33

# Check scrape lock status
sqlite3 instance/medal_pool.db "SELECT * FROM system_meta WHERE key = 'medal_scrape_in_progress';"
# Should show: false (when not scraping)

# Check last update time
sqlite3 instance/medal_pool.db "SELECT MAX(updated_at) FROM medals;"

# Force stale data (for testing)
sqlite3 instance/medal_pool.db "UPDATE medals SET updated_at = datetime('now', '-1 hour');"
```

---

## Troubleshooting

**Admin page not loading?**
- Make sure you're logged in with admin email (ken@corless.com)

**Auto-refresh not triggering?**
- Check contest state is "locked" or "complete"
- Verify MEDAL_STALENESS_SECONDS=10 in .env
- Make sure medal data is older than 10 seconds

**No Wikipedia section in admin panel?**
- Check wikipedia_medal_url is set in contest table
- Make sure you're on the singleauto branch

---

## Expected Results

✅ Manual refresh updates 15 countries
✅ Auto-refresh triggers after 10 seconds of staleness
✅ Total medals = 33 (11 gold, 11 silver, 11 bronze)
✅ Scrape metadata stored in system_meta
✅ Leaderboard shows correct rankings and points
