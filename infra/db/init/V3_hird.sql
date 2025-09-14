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
  predict_date        DATE NOT NULL,
  yhat                NUMERIC(14,4) NOT NULL,
  yhat_lower          NUMERIC(14,4),
  yhat_upper          NUMERIC(14,4),
  features_version    TEXT,
  model_artifact_uri  TEXT,
  created_at          TIMESTAMPTZ DEFAULT now()
);

-- Index for fast lookup by city, target, and horizon
CREATE INDEX IF NOT EXISTS idx_model_predictions_city_horizon_date
ON public.model_predictions (city, target, horizon_months, predict_date);


-- -----------------------------------------------------------------------------
-- Aggregated Time-Series Tables
-- These tables have composite primary keys (date, city/province).
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.house_price_index (
    date                    DATE,
    city                    VARCHAR(100),
    index_value             DECIMAL(10, 2),
    median_price_house      DECIMAL(12, 2),
    median_price_condo      DECIMAL(12, 2),
    active_listings_count   INTEGER,
    avg_listing_days        INTEGER,
    PRIMARY KEY (date, city)
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
    date                    DATE,
    city                    VARCHAR(100),
    population              INTEGER,
    net_migration           INTEGER,
    age_distribution_25_34_perc DECIMAL(5, 2),
    avg_disposable_income   DECIMAL(12, 2),
    PRIMARY KEY (date, city)
);


-- -----------------------------------------------------------------------------
-- Macro-Economic & Contextual Tables
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.macro_economic_data (
    date                DATE,
    province            VARCHAR(100),
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
