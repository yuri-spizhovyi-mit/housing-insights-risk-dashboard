-- V2: raw rental listings + helpful indexes
-- Purpose: store permitted scraped/ingested listings, then aggregate to monthly medians
-- Used by: ml/src/etl/market_listings.py

CREATE TABLE IF NOT EXISTS public.rent_listings_raw (
  id           TEXT PRIMARY KEY,                 -- stable hash per listing (e.g., sha256[:32])
  source       TEXT NOT NULL,                    -- e.g., 'VantageWest', 'Craigslist', 'ListingsFeedX'
  city         TEXT NOT NULL,                    -- canonical city: Kelowna | Vancouver | Toronto
  bedrooms     INT,                              -- 0,1,2,3,4 (use 4 to represent 4+)
  price        DOUBLE PRECISION,                 -- asking rent
  posted_at    TIMESTAMP WITH TIME ZONE,         -- when the listing was posted (if provided)
  captured_at  TIMESTAMP WITH TIME ZONE NOT NULL,-- when our ETL fetched the row
  url          TEXT,                             -- listing URL (for traceability)
  title        TEXT                              -- human-friendly title/snippet
);

-- Helpful indexes for common filters
CREATE INDEX IF NOT EXISTS idx_rent_listings_raw_city
  ON public.rent_listings_raw(city);

CREATE INDEX IF NOT EXISTS idx_rent_listings_raw_captured
  ON public.rent_listings_raw(captured_at);

-- (Optional) narrow index if you’ll aggregate frequently by city/month
-- CREATE INDEX IF NOT EXISTS idx_rent_listings_raw_city_posted_month
--   ON public.rent_listings_raw(city, date_trunc('month', COALESCE(posted_at, captured_at)));
