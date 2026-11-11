# Simplified Housing Insights MVP

The active dashboard uses the existing FastAPI `/cities`, `/forecast`, and `/risk` endpoints. No new database tables, snapshot publishing, model evaluation pipeline, or Alembic migrations are required for this release.

## Run locally

In `services/ui`, run `npm ci` and `npm run dev`. The default API is https://housing-insights-risk-dashboard.vercel.app. Set `VITE_API_BASE_URL` to use another existing API. No local database is needed to preview the frontend against that API.

For local API work, install `services/fapi/requirements.txt`, set DATABASE_URL to the existing development database, then run `python -m uvicorn services.fapi.main:app --port 8000`. The backend correctness changes use the existing tables.

## Included

- Responsive market overview and About the data page, light/dark themes.
- City, Price/Rent, horizon and model controls with URL restoration.
- Experimental forecast, reported bounds, accessible values table and dated summaries.
- Independently loaded risk indicators; composite score withheld.
- Strict response validation, timeout/cancellation, per-filter caching and retry controls.
- Backend fixes for latest risk observations, missing indicators, zero bounds and complete forecast series.

## Deferred

City comparison, PDF export, automatic model selection, v2 publications, generated v2 contracts, migrations and monitoring infrastructure. Previous exploratory files remain in the checkout for future work. V2 backend routes are disabled unless ENABLE_HOUSING_V2=true. They are not needed by the MVP.

## Checks and release

Run npm test, npm run lint, npm run build, and `python -m pytest services/fapi/tests -q`. Preview at 375, 768 and 1440 pixels. Check Calgary/Toronto/Vancouver, Price/Rent changes, unavailable models, API failures, and both themes.

Deploy existing-table backend fixes first, then deploy `services/ui/dist` to the existing frontend host. Set VITE_HOUSING_V2=false and rebuild to restore the original dashboard. Hosting credentials are required for deployment; no production changes have been performed from this checkout.

## Known data limits

The API does not expose verified units, training dates, or source freshness. The UI labels values as API scale and displays forecast periods, never pretending predictions are observed current prices. Captured public forecasts end in August 2026 and are historical as of November 2026. Refreshing the page does not retrain models or make that dataset current.
