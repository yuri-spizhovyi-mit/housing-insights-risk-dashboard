--
-- Database Schema for the Housing Insights + Risk Dashboard
--
-- This script creates all the necessary tables for the MVP, including raw data,
-- feature-engineered data, aggregated time-series, and model predictions.
--

-- Enable the uuid-ossp extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------------------------
-- Aggregated Time-Series Tables
-- These tables have composite primary keys (date, city/province).
-- -----------------------------------------------------------------------------

-- CREA HPI table (MLS® Home Price Index)
CREATE TABLE IF NOT EXISTS public.house_price_index (
    date DATE NOT NULL,
    city TEXT NOT NULL,
    property_type TEXT NOT NULL,
    benchmark_price NUMERIC,
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (date, city, property_type)
);

-- -----------------------------------------------------------------------------
-- 📊 Table: public.metrics
-- Purpose: Store monthly national or city-level economic indicators
--           (e.g., mortgage rates, overnight rate, unemployment, CPI)
-- Frequency: Monthly (YYYY-MM-01)
-- Grain: One observation per (date, city, metric)
-- -----------------------------------------------------------------------------
-- Data Source(s):
--   • Bank of Canada (BoC)  – Overnight rate (V39079), 5-year mortgage rate (V80691335)
--   • Statistics Canada     – Unemployment rate and other labour indicators
--   • Internal CSV/ETL      – Optional additional metrics
-- -----------------------------------------------------------------------------
-- Schema Reference: Data_ETL Section 2.4 — Destination Table
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.metrics (
    date DATE NOT NULL,                -- Month start (YYYY-MM-01)
    city TEXT NOT NULL,                -- Region or national aggregate ('Canada' if national)
    metric TEXT NOT NULL,              -- Metric name (e.g., 'mortgage_rate', 'overnight_rate', 'unemployment_rate')
    value NUMERIC,                     -- Metric numeric value (e.g., 5.25)
    source TEXT DEFAULT 'unknown',     -- Data source identifier (e.g., 'BoC_V39079', 'StatsCan_14-10-0287')
    created_at TIMESTAMPTZ DEFAULT now(), -- Record ingestion timestamp
    PRIMARY KEY (date, city, metric)
);

COMMENT ON TABLE public.metrics IS
    'Stores monthly economic indicators such as mortgage rate, overnight rate, and unemployment rate used as features in housing forecasts.';

COMMENT ON COLUMN public.metrics.date IS
    'Month start date (YYYY-MM-01) — all series aligned to monthly frequency.';

COMMENT ON COLUMN public.metrics.city IS
    'Geographic level of observation (e.g., Toronto, Vancouver, or Canada for national series).';

COMMENT ON COLUMN public.metrics.metric IS
    'Canonical metric name (mortgage_rate, overnight_rate, unemployment_rate, etc.).';

COMMENT ON COLUMN public.metrics.value IS
    'Numeric value of the metric (in percent or raw index units depending on source).';

COMMENT ON COLUMN public.metrics.source IS
    'Source identifier for traceability (e.g., BoC series code, StatsCan table ID).';

COMMENT ON COLUMN public.metrics.created_at IS
    'Timestamp of record creation in database.';

-- -----------------------------------------------------------------------------
-- 🏙️  Table: public.rent_index
-- Purpose:
--   Store annual CMHC/StatCan rent survey data normalized to monthly grain.
--   Each row represents rent metrics for a (date, city, unit_type).
-- -----------------------------------------------------------------------------

DROP TABLE IF EXISTS public.rent_index CASCADE;

CREATE TABLE public.rent_index (
    date          DATE        NOT NULL,           -- Month start (YYYY-MM-01)
    city          TEXT        NOT NULL,           -- City / CMA name
    rent_value    NUMERIC(10,2),                  -- Average monthly rent (CAD)
    data_flag     TEXT,                           -- ORIG_ANNUAL, DERIVED_ANNUAL, LOCF_FROM_2024
    source        TEXT DEFAULT 'CMHC_Rental_Market_Survey',
    last_seen     TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (date, city)
);

-- -----------------------------------------------------------------------------
-- Comments for documentation
-- -----------------------------------------------------------------------------
COMMENT ON TABLE public.rent_index IS
    'Annual CMHC/StatCan rent data normalized to monthly grain (date=YYYY-MM-01).';

COMMENT ON COLUMN public.rent_index.date IS
    'Canonical date (month start). Annual values expanded to monthly rows when used in features.';

COMMENT ON COLUMN public.rent_index.city IS
    'Municipality or CMA name normalized to match CREA city names.';

COMMENT ON COLUMN public.rent_index.rent_value IS
    'Average monthly rent (CAD) for the given unit_type and city.';

COMMENT ON COLUMN public.rent_index.data_flag IS
    'Indicates data provenance: ORIG_ANNUAL, DERIVED_ANNUAL, LOCF_FROM_2024.';

COMMENT ON COLUMN public.rent_index.source IS
    'Original dataset reference (e.g. CMHC_Rental_Market_Survey_2024).';

COMMENT ON COLUMN public.rent_index.last_seen IS
    'Timestamp of ETL load or update.';

-- -----------------------------------------------------------------------------
-- Table: public.demographics
-- Purpose: Store demographic data for each city and date.
-- Frequency: Monthly (YYYY-MM-01)
-- Grain: One observation per (date, city)
-- -----------------------------------------------------------------------------
-- Data Source(s):
--   • Statistics Canada     – Population, migration, and income data
--   • Internal CSV/ETL      – Optional additional metrics
-- -----------------------------------------------------------------------------
-- Schema Reference: Data_ETL Section 2.4 — Destination Table
-- -----------------------------------------------------------------------------
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.demographics (
    date                DATE NOT NULL,
    city                VARCHAR(100) NOT NULL,
    population          INTEGER,
    migration_rate      NUMERIC(6,2),          -- percentage or per-1000 rate
    median_income       NUMERIC(12,2),         -- median household income
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (date, city)
);
    

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


-- ------------------------------------------------------------
-- Migration: V10__create_features_table_with_property_type.sql
-- Purpose: Central feature store for housing models (property_type aware)
-- ------------------------------------------------------------

DROP TABLE IF EXISTS public.features CASCADE;

CREATE TABLE public.features (
    date DATE NOT NULL,
    city TEXT NOT NULL,
    property_type TEXT NOT NULL,

    -- Housing data
    hpi_benchmark NUMERIC(14,2),
    hpi_change_yoy NUMERIC(6,3),
    rent_avg_city NUMERIC(14,2),
    rent_change_yoy NUMERIC(6,3),

    -- Economic metrics
    mortgage_rate NUMERIC(6,3),
    unemployment_rate NUMERIC(6,3),
    overnight_rate NUMERIC(6,3),

    -- Demographics
    population BIGINT,
    median_income NUMERIC(14,2),

    -- Listings
    listings_count INT,
    new_listings INT,
    sales_to_listings_ratio NUMERIC(6,3),

    -- Macro context
    gdp_growth NUMERIC(6,3),
    cpi_yoy NUMERIC(6,3),
    migration_rate DOUBLE PRECISION,

    -- Metadata
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (date, city, property_type)
);

COMMENT ON TABLE public.features IS
    'Aggregated feature store combining housing, rent, economic, demographic, and macro data by city, month, and property type.';

-- Migration V5: Create model_features table
-- ----------------------------------------------------------
-- Holds normalized, model-ready features derived from public.features
-- Used by Prophet, ARIMA, and LightGBM forecasting modules

DROP TABLE IF EXISTS public.model_features;

CREATE TABLE public.model_features (
    city TEXT NOT NULL,
    date DATE NOT NULL,

    -- core raw features
    hpi_benchmark DOUBLE PRECISION,
    rent_avg_city DOUBLE PRECISION,
    mortgage_rate DOUBLE PRECISION,
    unemployment_rate DOUBLE PRECISION,
    overnight_rate DOUBLE PRECISION,
    population DOUBLE PRECISION,
    median_income DOUBLE PRECISION,
    migration_rate DOUBLE PRECISION,
    gdp_growth DOUBLE PRECISION,
    cpi_yoy DOUBLE PRECISION,

    -- YoY features
    hpi_benchmark_yoy DOUBLE PRECISION,
    rent_avg_city_yoy DOUBLE PRECISION,

    -- lag features
    lag_1 DOUBLE PRECISION,
    lag_3 DOUBLE PRECISION,
    lag_6 DOUBLE PRECISION,

    -- rolling features
    roll_3 DOUBLE PRECISION,
    roll_6 DOUBLE PRECISION,

    -- Z-score normalized features
    hpi_benchmark_z DOUBLE PRECISION,
    rent_avg_city_z DOUBLE PRECISION,
    mortgage_rate_z DOUBLE PRECISION,
    unemployment_rate_z DOUBLE PRECISION,
    overnight_rate_z DOUBLE PRECISION,
    population_z DOUBLE PRECISION,
    median_income_z DOUBLE PRECISION,
    migration_rate_z DOUBLE PRECISION,
    gdp_growth_z DOUBLE PRECISION,
    cpi_yoy_z DOUBLE PRECISION,
    hpi_benchmark_yoy_z DOUBLE PRECISION,
    rent_avg_city_yoy_z DOUBLE PRECISION,
    lag_1_z DOUBLE PRECISION,
    lag_3_z DOUBLE PRECISION,
    lag_6_z DOUBLE PRECISION,
    roll_3_z DOUBLE PRECISION,
    roll_6_z DOUBLE PRECISION,

    -- metadata
    etl_version TEXT,
    processed_at TIMESTAMP WITH TIME ZONE
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





-- ------------------------------------------------------------
-- Migration: V4__macro_economic_data.sql
-- Purpose : Create table for GDP growth and CPI YoY
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.macro_economic_data (
    date DATE NOT NULL,
    city VARCHAR(100) NOT NULL,
    gdp_growth NUMERIC(6,3),
    cpi_yoy NUMERIC(6,3),
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (date, city)
);

-- Optional index to speed up joins by date
CREATE INDEX IF NOT EXISTS idx_macro_data_date_city
    ON public.macro_economic_data (date, city);

COMMENT ON TABLE public.macro_economic_data IS
    'Monthly macroeconomic indicators (GDP growth %, CPI YoY %) per city, 2005–2025.';
COMMENT ON COLUMN public.macro_economic_data.gdp_growth IS
    'Monthly real GDP growth rate (%, broadcasted from national or provincial data).';
COMMENT ON COLUMN public.macro_economic_data.cpi_yoy IS
    'Consumer Price Index year-over-year inflation rate (%), broadcasted from provincial CPI.';



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

CREATE TABLE IF NOT EXISTS public.model_comparison (
    city TEXT NOT NULL,
    horizon_months INTEGER NOT NULL,
    model_name TEXT NOT NULL,
    mae DOUBLE PRECISION,
    mape DOUBLE PRECISION,
    rmse DOUBLE PRECISION,
    rank INTEGER,
    best_model BOOLEAN DEFAULT FALSE,
    evaluated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT model_comparison_pk PRIMARY KEY (city, horizon_months, model_name)
);
