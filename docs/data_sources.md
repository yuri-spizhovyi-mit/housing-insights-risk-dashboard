# Data Sources

## CREA — MLS® Home Price Index (HPI)

- **What:** Monthly city-level HPI / benchmark prices.
- **Access:** HPI tool “Accept and download data” link → monthly ZIP (`MLS_HPI_<Month>_<Year>.zip`).
- **URL pattern origin:** HPI tool page (we programmatically extract the latest ZIP link).
- **Transform:** Keep `city`,`date`,`index_value` with `measure ∈ {benchmark_price | hpi_index}`; date floored to month.
- **Load:** `public.house_price_index` (measure marks what we loaded).  
  Source ref: CREA HPI tool download link exists on the HPI page. :contentReference[oaicite:10]{index=10}

## CMHC (via StatCan CODR/WDS)

- **5-year conventional mortgage rate:** Table **34-10-0145-01** (monthly).  
  WDS: `getFullTableDownloadCSV/3410014501/en` → CSV ZIP.  
  **Metric key:** `mortgage_5y_conventional` → `public.metrics`.  
  Source refs: table page; WDS user guide. :contentReference[oaicite:11]{index=11}

## StatCan macros

- **CPI all-items:** Table **18-10-0004-01** (monthly; has CMA geographies).  
  WDS: `getFullTableDownloadCSV/1810000401/en` → CSV ZIP.  
  **Metric key:** `cpi_all_items` (Kelowna/Vancouver/Toronto CMAs) → `public.metrics`.  
  Source refs: table page; WDS user guide. :contentReference[oaicite:12]{index=12}

- _(Optional next)_ Average weekly earnings / unemployment: Tables **14-10-0223-01** or **14-10-0220-01** (monthly). Same WDS pattern. :contentReference[oaicite:13]{index=13}

## Bank of Canada — Valet API

- **Policy rate (target for the overnight rate):** series **V39079**.  
  Valet: `/valet/observations/V39079/json?start_date=YYYY-MM-DD`.  
  **Metric key:** `policy_rate_overnight` → `public.metrics`.  
  Source refs: Valet docs; series code reference (V39079). :contentReference[oaicite:14]{index=14}

## Rentals.ca (monthly city rents)

- **What:** Monthly National Rent Report with city tables (no official CSV API).
- **Access:** Scrape the report page and parse the first city table for Vancouver/Toronto/Kelowna.
- **Metric:** `public.rents` with `bedroom_type='overall'`.
- **Note:** Replace with formal feed if provided later. Source ref: report page. :contentReference[oaicite:15]{index=15}
