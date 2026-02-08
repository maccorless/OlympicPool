-- Migration: Add wikipedia_medal_url column to events table
-- Date: 2026-02-08
-- Description: Adds support for Wikipedia medal table scraping

-- Add wikipedia_medal_url column to events table
ALTER TABLE events ADD COLUMN wikipedia_medal_url TEXT;

-- Example: Update existing event with Wikipedia URL
-- UPDATE events SET wikipedia_medal_url = 'https://en.wikipedia.org/wiki/2026_Winter_Olympics_medal_table' WHERE slug = 'milano-2026';
