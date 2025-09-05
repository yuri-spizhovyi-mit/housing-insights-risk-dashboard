-- Minimal ETL tables for MVP

CREATE TABLE IF NOT EXISTS public.metrics (
  city TEXT NULL,
  date DATE NOT NULL,
  metric TEXT NOT NULL,
  value DOUBLE PRECISION NOT NULL,
  source TEXT NOT NULL,
  PRIMARY KEY (date, metric, city)
);

CREATE TABLE IF NOT EXISTS public.house_price_index (
  city TEXT NOT NULL,
  date DATE NOT NULL,
  index_value DOUBLE PRECISION NOT NULL,
  measure TEXT NOT NULL,
  source TEXT NOT NULL,
  PRIMARY KEY (city, date, measure)
);

CREATE TABLE IF NOT EXISTS public.rents (
  city TEXT NOT NULL,
  date DATE NOT NULL,
  bedroom_type TEXT NULL,
  median_rent DOUBLE PRECISION NOT NULL,
  source TEXT NOT NULL,
  PRIMARY KEY (city, date, COALESCE(bedroom_type,'overall'))
);
