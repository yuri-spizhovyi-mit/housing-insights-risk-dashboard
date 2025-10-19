--
-- Database Schema for the Housing Insights + Risk Dashboard
--
-- This script creates all the necessary tables for the MVP, including raw data,
-- feature-engineered data, aggregated time-series, and model predictions.
--

-- Enable the uuid-ossp extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------------------------
-- Raw Data Tables
-- These tables are the initial "dump" from data collection.
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.listings_raw (
    listing_id      VARCHAR(255) PRIMARY KEY,
    url             TEXT,
    date_posted     DATE,
    city            VARCHAR(100),
    postal_code     VARCHAR(20),
    property_type   VARCHAR(50),
    listing_type    VARCHAR(10),
    price           DECIMAL(12, 2),
    bedrooms        INTEGER,
    bathrooms       INTEGER,
    area_sqft       INTEGER,
    year_built      INTEGER,
    description     TEXT
);

-- Index for efficient lookup by postal code and city
CREATE INDEX IF NOT EXISTS idx_listings_raw_geo
ON public.listings_raw (city, postal_code);


-- -----------------------------------------------------------------------------
-- Processed & Feature-Engineered Data Tables
-- These tables are the direct output of the ETL process.
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.listings_features (
    listing_id              VARCHAR(255) PRIMARY KEY,
    price_per_sqft          DECIMAL(12, 2),
    property_age            INTEGER,
    bedrooms                INTEGER,
    bathrooms               INTEGER,
    area_sqft               INTEGER,
    year_built              INTEGER,
    postal_code             VARCHAR(20),
    property_type_house     BOOLEAN,
    property_type_condo     BOOLEAN,
    property_type_apartment BOOLEAN,
    property_type_townhouse BOOLEAN,
    -- Add more one-hot encoded features as needed
    CONSTRAINT fk_listings_features_listing_id
        FOREIGN KEY (listing_id) REFERENCES public.listings_raw(listing_id)
);


-- -----------------------------------------------------------------------------
-- Serving-layer predictions cache
-- This table stores pre-computed forecasts to serve the API.
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.model_predictions (
  run_id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  model_name          TEXT NOT NULL,
  target              TEXT NOT NULL,
  horizon_months      INTEGER NOT NULL,
  city                TEXT NOT NULL,
  property_type       TEXT,
  beds                INTEGER,
  baths               INTEGER,
  sqft_min            INTEGER,
  sqft_max            INTEGER,
  year_built_min      INTEGER,
  year_built_max      INTEGER,
  predict_date        DATE NOT NULL,
  yhat                NUMERIC(14,4) NOT NULL,
  yhat_lower          NUMERIC(14,4),
  yhat_upper          NUMERIC(14,4),
  features_version    TEXT,
  model_artifact_uri  TEXT,
  created_at          TIMESTAMPTZ DEFAULT now(),
  is_micro            BOOLEAN
);

CREATE INDEX IF NOT EXISTS idx_model_predictions_city_horizon_date
ON public.model_predictions (city, target, horizon_months, predict_date);


-- -----------------------------------------------------------------------------
-- Aggregated Time-Series Tables
-- These tables have composite primary keys (date, city/province).
-- -----------------------------------------------------------------------------

-- CREA HPI table (MLS® Home Price Index)
CREATE TABLE IF NOT EXISTS public.house_price_index (
    city          VARCHAR(100)    NOT NULL,
    "date"        DATE            NOT NULL,
    index_value   DOUBLE PRECISION,
    measure       VARCHAR(100)    NOT NULL,
    source        VARCHAR(50)     NOT NULL,
    CONSTRAINT house_price_index_pkey PRIMARY KEY (city, "date", measure)
);


CREATE TABLE IF NOT EXISTS public.rent_index (
    date                        DATE,
    city                        VARCHAR(100),
    index_value                 DECIMAL(10, 2),
    median_rent_apartment_1br   DECIMAL(12, 2),
    median_rent_apartment_2br   DECIMAL(12, 2),
    median_rent_apartment_3br   DECIMAL(12, 2),
    active_rental_count         INTEGER,
    avg_rental_days             INTEGER,
    PRIMARY KEY (date, city)
);


CREATE TABLE IF NOT EXISTS public.demographics (
    date                DATE NOT NULL,
    city                VARCHAR(100) NOT NULL,
    population          INTEGER,
    migration_rate      NUMERIC(6,2),          -- percentage or per-1000 rate
    age_25_34_perc      NUMERIC(5,2),          -- share of population age 25–34
    median_income       NUMERIC(12,2),         -- median household income
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (date, city)
);


-- -----------------------------------------------------------------------------
-- Macro-Economic & Contextual Tables
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS public.macro_economic_data CASCADE;
CREATE TABLE IF NOT EXISTS public.macro_economic_data (
    date                DATE,
    city            VARCHAR(100),
    unemployment_rate   DECIMAL(5, 2),
    gdp_growth_rate     DECIMAL(5, 2),
    prime_lending_rate  DECIMAL(5, 2),
    housing_starts      INTEGER,
    PRIMARY KEY (date, province)
);


CREATE TABLE IF NOT EXISTS public.news_sentiment (
    date                DATE,
    city                VARCHAR(100),
    sentiment_score     DECIMAL(5, 2),
    sentiment_label     VARCHAR(20),
    PRIMARY KEY (date, city)
);

-- V3__news_articles.sql
CREATE TABLE IF NOT EXISTS public.news_articles (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    city VARCHAR(100),
    title TEXT NOT NULL,
    url TEXT,
    sentiment_score DECIMAL(5,2),
    sentiment_label VARCHAR(20) CHECK (sentiment_label IN ('POS','NEG','NEU'))
);

-- Helpful index for queries
CREATE INDEX idx_news_articles_city_date
    ON public.news_articles (city, date DESC);


CREATE TABLE IF NOT EXISTS public.construction_permits (
    permit_id       VARCHAR(255) PRIMARY KEY,
    city            VARCHAR(100),
    postal_code     VARCHAR(20),
    units_approved  INTEGER,
    date_approved   DATE,
    property_type   VARCHAR(50)
);

-- Index on postal_code to support joins with `listings_raw`
CREATE INDEX IF NOT EXISTS idx_construction_permits_postal_code
ON public.construction_permits (postal_code);

-- V3__risk_predictions.sql
CREATE TABLE IF NOT EXISTS public.risk_predictions (
  run_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  city TEXT NOT NULL,
  risk_type TEXT NOT NULL,         -- affordability, volatility, price_to_rent, etc.
  predict_date DATE NOT NULL,
  risk_value NUMERIC(14,4) NOT NULL,
  model_name TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

--V4__anomaly_signals.sql
-- Optional index for fast dashboard queries
CREATE INDEX IF NOT EXISTS idx_risk_predictions_city_date
  ON public.risk_predictions(city, predict_date);

CREATE TABLE IF NOT EXISTS public.anomaly_signals (
  run_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  city TEXT NOT NULL,
  target TEXT NOT NULL,            -- "price" or "rent"
  detect_date DATE NOT NULL,
  anomaly_score NUMERIC(14,4),
  is_anomaly BOOLEAN DEFAULT false,
  model_name TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_anomaly_signals_city_target_date
  ON public.anomaly_signals(city, target, detect_date);

CREATE TABLE IF NOT EXISTS public.metrics (
    id SERIAL PRIMARY KEY,
    city TEXT NOT NULL,
    date DATE NOT NULL,
    metric TEXT NOT NULL,
    value NUMERIC,
    source TEXT DEFAULT 'unknown',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- V5__features.sql
-- -----------------------------------------------------------------------------
-- Macro-level Feature Table for Forecasting, Risk, and Anomaly Models
-- -----------------------------------------------------------------------------
-- Purpose:
--   Aggregates ETL outputs (HPI, rents, metrics) into a city-date feature table
--   consumed by modeling layer (Prophet, ARIMA, Isolation Forest, etc.).
-- -----------------------------------------------------------------------------

DROP TABLE IF EXISTS public.features CASCADE;

CREATE TABLE public.features (
    -- --- Keys ---------------------------------------------------------------
    date                DATE            NOT NULL,
    city                VARCHAR(100)    NOT NULL,

    -- --- Target Variables (Rent & HPI) -------------------------------------
    price_avg           NUMERIC(14, 2),         -- average rent price per month
    rent_index          NUMERIC(12, 2),         -- median rent per city-month
    hpi_composite_sa    DOUBLE PRECISION,
    hpi_apartment_sa    DOUBLE PRECISION,
    hpi_townhouse_sa    DOUBLE PRECISION,

    -- --- Macro Indicators (BoC + StatCan) ----------------------------------
    overnightrate       NUMERIC(8, 4),
    primerate           NUMERIC(8, 4),
    cpi_allitems        NUMERIC(10, 3),
    unemploymentrate    NUMERIC(8, 3),
    gdp_growthrate      NUMERIC(8, 3),

    -- --- Micro-Level (Property-Specific) -----------------------------------
    bedrooms_avg        NUMERIC(4, 1),
    bathrooms_avg       NUMERIC(4, 1),
    sqft_avg            NUMERIC(12, 2),
    property_type       TEXT,

    -- --- Derived & Engineered Features -------------------------------------
    price_to_rent       DOUBLE PRECISION,       -- hpi_composite_sa / rent_index
    price_to_sqft       DOUBLE PRECISION,       -- price_avg / sqft_avg
    price_mom_pct       DOUBLE PRECISION,       -- MoM growth of avg price
    rent_mom_pct        DOUBLE PRECISION,       -- MoM growth of rent index
    hpi_mom_pct         DOUBLE PRECISION,       -- MoM growth of HPI composite

    -- --- Metadata -----------------------------------------------------------
    features_version    TEXT DEFAULT 'v2.0',
    created_at          TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT features_pkey PRIMARY KEY (date, city)
);




-- Helpful index for dashboard/model queries by city/date
CREATE INDEX IF NOT EXISTS idx_features_city_date
    ON public.features (city, date DESC);

COMMENT ON TABLE public.features IS
    'Macro-level engineered features used for forecasting, risk, and anomaly models.';

COMMENT ON COLUMN public.features.hpi_composite_sa IS
    'Composite MLS® Home Price Index, seasonally adjusted.';
COMMENT ON COLUMN public.features.rent_index IS
    'Synthetic or aggregated rent index (median or benchmark).';
COMMENT ON COLUMN public.features.price_to_rent IS
    'Computed ratio of HPI to Rent Index.';
COMMENT ON COLUMN public.features.features_version IS
    'Version tag of feature schema to track evolution.';
