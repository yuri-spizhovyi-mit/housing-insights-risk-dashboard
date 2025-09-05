# Data Sources (ETL Overview)

## CREA

- What: Benchmark home prices / HPI by city, monthly
- Fields: city, date, benchmark_price
- Loaded to: public.house_price_index (measure='benchmark_price', source='CREA')

## CMHC / Rentals.ca

- What: Rents by bedroom type, monthly
- Fields: city, date, bedroom_type, median_rent
- Loaded to: public.rents (source='CMHC')

## StatCan

- What: Macro series (CPI, wages, population, etc.)
- Fields: date, metric, value, city (nullable)
- Loaded to: public.metrics (source='StatCan')

## Bank of Canada

- What: Policy/overnight rate, mortgage rates, yields
- Fields: date, metric, value (city=NULL)
- Loaded to: public.metrics (source='BoC')
