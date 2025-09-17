-- db/seed.sql
-- Minimal seed for the Housing Insights + Risk Dashboard (Kelowna examples)

BEGIN;

-- 1) Raw listing (Rental)
INSERT INTO public.listings_raw (
    listing_id, url, date_posted, city, postal_code, property_type, listing_type,
    price, bedrooms, bathrooms, area_sqft, year_built, description
) VALUES
    ('seed-listing-001',
     'https://example.com/kelowna/apt-1br-seed',
     '2025-07-02', 'Kelowna', 'V1Y 1A1', 'Apartment', 'Rental',
     1850.00, 1, 1, 550, 2012, 'Cozy 1BR in downtown Kelowna')
ON CONFLICT (listing_id) DO NOTHING;

-- 2) Features for the listing (1:1)
INSERT INTO public.listings_features (
    listing_id, price_per_sqft, property_age, bedrooms, bathrooms, area_sqft,
    year_built, postal_code, property_type_house, property_type_condo, property_type_apartment
) VALUES
    ('seed-listing-001', 3.36, 13, 1, 1, 550, 2012, 'V1Y 1A1',
     FALSE, FALSE, TRUE)
ON CONFLICT (listing_id) DO NOTHING;

-- 3) Aggregated Time-Series: House Price Index (two months)
INSERT INTO public.house_price_index (
    date, city, index_value, median_price_house, median_price_condo,
    active_listings_count, avg_listing_days
) VALUES
    ('2025-06-01','Kelowna',243.50, 875000.00, 515000.00, 1220, 27),
    ('2025-07-01','Kelowna',245.10, 885000.00, 520000.00, 1185, 26)
ON CONFLICT (date, city) DO NOTHING;

-- 4) Aggregated Time-Series: Rent Index (one month)
INSERT INTO public.rent_index (
    date, city, index_value, median_rent_apartment_1br, median_rent_apartment_2br,
    median_rent_apartment_3br, active_rental_count, avg_rental_days
) VALUES
    ('2025-07-01','Kelowna',108.20, 1850.00, 2300.00, 2900.00, 640, 24)
ON CONFLICT (date, city) DO NOTHING;

-- 5) Aggregated Time-Series: Demographics (annual-ish sample)
INSERT INTO public.demographics (
    date, city, population, net_migration, age_distribution_25_34_perc, avg_disposable_income
) VALUES
    ('2025-01-01','Kelowna', 157000, 2300, 16.40, 45750.00)
ON CONFLICT (date, city) DO NOTHING;

-- 6) Macro-Economic (provincial snapshot)
INSERT INTO public.macro_economic_data (
    date, province, unemployment_rate, gdp_growth_rate, prime_lending_rate, housing_starts
) VALUES
    ('2025-07-01','British Columbia', 5.60, 1.40, 6.95, 3100)
ON CONFLICT (date, province) DO NOTHING;

-- 7) News sentiment (city snapshot)
INSERT INTO public.news_sentiment (
    date, city, sentiment_score, sentiment_label
) VALUES
    ('2025-07-01','Kelowna', 0.12, 'Neutral')
ON CONFLICT (date, city) DO NOTHING;

-- 8) Construction permits (simple example)
INSERT INTO public.construction_permits (
    permit_id, city, postal_code, units_approved, date_approved, property_type
) VALUES
    ('PRM-KELOWNA-0001','Kelowna','V1Y 1A1', 48, '2025-06-15','Apartment')
ON CONFLICT (permit_id) DO NOTHING;

-- 9) Serving-layer predictions cache (two months)
-- Note: your schema set PRIMARY KEY on run_id (UUID DEFAULT gen_random_uuid()).
-- We provide explicit UUIDs via uuid-ossp (uuid_generate_v4()) which is enabled in your DDL.
INSERT INTO public.model_predictions (
    run_id, model_name, target, horizon_months, city, predict_date,
    yhat, yhat_lower, yhat_upper, features_version, model_artifact_uri, created_at
) VALUES
    (uuid_generate_v4(), 'lgbm_price_kelowna_v1', 'rent', 1, 'Kelowna', '2025-08-01',
     1865.0000, 1770.0000, 1960.0000, 'feat-v1', 's3://minio/models/lgbm_price_kelowna_v1', now()),
    (uuid_generate_v4(), 'lgbm_price_kelowna_v1', 'rent', 1, 'Kelowna', '2025-09-01',
     1878.0000, 1784.0000, 1975.0000, 'feat-v1', 's3://minio/models/lgbm_price_kelowna_v1', now())
ON CONFLICT (run_id) DO NOTHING;

COMMIT;
