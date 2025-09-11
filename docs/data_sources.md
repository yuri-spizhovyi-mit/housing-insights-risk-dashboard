# Data Sources — Housing Insights + Risk Dashboard

This document describes the external data sources integrated into the ETL pipelines, how they are normalized, where raw snapshots are stored, and how data lands in Postgres.

---

## CREA (Canadian Real Estate Association)

- **Source / Endpoint**: CREA HPI portal (CSV download)
- **Snapshot Location**: `minio://hird-raw/raw/crea/{YYYY-MM-DD}/...`
- **Normalized Mapping → `public.house_price_index`**

  | Field         | From                                              |
  | ------------- | ------------------------------------------------- |
  | `city`        | CMA name (e.g., Kelowna, Vancouver, Toronto)      |
  | `date`        | Report month                                      |
  | `index_value` | HPI value                                         |
  | `measure`     | Benchmark type (e.g., Composite, Single-Detached) |
  | `source`      | `"CREA"`                                          |

- **Primary Key / Grain**: `(city, date, measure)`
- **Cadence**: Monthly
- **Backfill**: Download full historical HPI CSVs and re-run adapter with earlier `--date`.
- **Caveats**: Benchmark coverage varies by CMA; not all property types exist in all cities.

---

## CMHC (Canada Mortgage and Housing Corporation)

- **Source / Endpoint**: StatCan/CMHC joint tables (CSV via StatCan WDS)
- **Snapshot Location**: `minio://hird-raw/raw/cmhc/{YYYY-MM-DD}/...`
- **Normalized Mapping → `public.metrics`**

  | Field    | From                                                          |
  | -------- | ------------------------------------------------------------- |
  | `city`   | CMA name (Kelowna, Vancouver, Toronto, Canada aggregate)      |
  | `date`   | Report period (month)                                         |
  | `metric` | Series name (e.g., CMHC_Series, Housing Starts, Vacancy Rate) |
  | `value`  | Observed value                                                |
  | `source` | `"StatCan/CMHC"`                                              |

- **Primary Key / Grain**: `(date, metric, city)`
- **Cadence**: Monthly / Quarterly depending on table
- **Backfill**: Download full WDS CSV and re-ingest.
- **Caveats**: Some series not available for all CMAs; frequency differs across metrics.

---

## Statistics Canada (StatCan)

- **Source / Endpoint**: StatCan Web Data Service (WDS) → full CSV by PID  
  Example: `https://www150.statcan.gc.ca/t1/wds/rest/getFullTableDownloadCSV/1810000401/en`
- **PID Integrated**: `1810000401` → **StatCan_CPI_AllItems**
- **Snapshot Location**:
  - Raw CSV: `minio://hird-raw/raw/statcan/{YYYY-MM-DD}/1810000401.csv`
  - Tidy CSV: `minio://hird-raw/raw/statcan/{YYYY-MM-DD}/1810000401.tidy.csv`
- **Normalized Mapping → `public.metrics`**

  | Field    | From                                                                       |
  | -------- | -------------------------------------------------------------------------- |
  | `date`   | `REF_DATE` (month-floored)                                                 |
  | `metric` | `"StatCan_CPI_AllItems"`                                                   |
  | `city`   | `GEO` (Kelowna (CMA), Vancouver (CMA), Toronto (CMA); fallback `"Canada"`) |
  | `value`  | `VALUE`                                                                    |
  | `source` | `"StatCan_1810000401"`                                                     |

- **Primary Key / Grain**: `(date, metric, city)`
- **Cadence**: Monthly
- **Backfill**: Re-run adapter with earlier `--date` or override `START_DATE`/`END_DATE`.
- **Caveats**: Some StatCan PIDs have different dimension structures (e.g., “Products”); filter applied to keep `All-items`.

---

## Bank of Canada (BoC)

- **Source / Endpoint**: BoC Valet API — `/valet/observations/{seriesNames}/json`  
  Example: `/valet/observations/V39079/json?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
- **Series IDs Integrated**:
  - `V39079` → **BoC_OvernightRate** (Target Overnight Rate)
- **Snapshot Location**: `minio://hird-raw/raw/boc/{YYYY-MM-DD}/V39079.tidy.csv`
- **Normalized Mapping → `public.metrics`**

  | Field    | From                              |
  | -------- | --------------------------------- |
  | `date`   | `observations[].d`                |
  | `metric` | `"BoC_OvernightRate"` (via alias) |
  | `city`   | `"Canada"`                        |
  | `value`  | `observations[].V39079.v`         |
  | `source` | `"BoC"`                           |

- **Primary Key / Grain**: `(date, metric, city)`
- **Cadence**: Daily (business days)
- **Backfill**: Set `START_DATE` and `END_DATE` environment variables or CLI flags.
- **Caveats**: No weekend/holiday values; some series have structural breaks.

---

## Rentals.ca

- **Source / Endpoint**:
  - **Version A (file)**: Local CSV or JSON (`Month, City, Bedroom, AverageRent`)
  - **Version B (endpoint)**: Rentals.ca API via proxy (`rentals_url_builder`)
- **Snapshot Location**:
  - File tidy: `minio://hird-raw/raw/rentals/{YYYY-MM-DD}/file.tidy.csv`
  - Endpoint tidy: `minio://hird-raw/raw/rentals/{YYYY-MM-DD}/endpoint.tidy.csv`
- **Normalized Mapping → `public.rents`**

  | Field          | From                                            |
  | -------------- | ----------------------------------------------- |
  | `city`         | `City` (mapped to canonical names)              |
  | `date`         | `Month`                                         |
  | `bedroom_type` | `Bedroom` (mapped: overall, 0BR, 1BR, 2BR, 3BR) |
  | `median_rent`  | `AverageRent`                                   |
  | `source`       | `"Rentals.ca_File"` or `"Rentals.ca_API"`       |

- **Primary Key / Grain**: `(city, "date", bedroom_type)`
- **Cadence**: Monthly
- **Backfill**: Use Version A (file) with historical CSVs; Version B for ongoing loads.
- **Caveats**: API requires proxy/authentication; mapping of bedroom types must be consistent.

---

## Orchestration

- **Pipeline runner**: `ml/pipelines/daily_ingest.py`  
  Runs adapters in order: CREA → CMHC → StatCan → BoC → Rentals
- **Make targets**:
  - `make etl` — run all sources for today
  - `make etl-boc` — run BoC only
  - `make etl-statcan` — run StatCan only
  - `make etl-rentals-file` — run Rentals from local file
  - `make etl-backfill-boc` — run BoC with backfill window

---

## Validation

Key SQL checks:

```sql
-- PK uniqueness
SELECT 'metrics' AS tbl, COUNT(*) total, COUNT(DISTINCT (date, metric, city)) uniq FROM public.metrics
UNION ALL
SELECT 'house_price_index', COUNT(*), COUNT(DISTINCT (city, date, measure)) FROM public.house_price_index
UNION ALL
SELECT 'rents', COUNT(*), COUNT(DISTINCT (city, "date", bedroom_type)) FROM public.rents;

-- Latest available date per metric
SELECT metric, MAX(date) AS last_date FROM public.metrics GROUP BY metric;

-- Freshness snapshot for BoC + StatCan CPI
SELECT metric, MAX(date) AS last_date
FROM public.metrics
WHERE metric IN ('BoC_OvernightRate', 'StatCan_CPI_AllItems')
GROUP BY metric;
```
