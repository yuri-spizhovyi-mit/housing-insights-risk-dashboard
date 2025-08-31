# Housing Insights + Risk Dashboard

**MVP (Sept–Nov 2025)**  
Team: Yuri (ML & Data Engineering) · Max (API & Frontend)

## Judge Mode (quickstart)
```bash
make judge
# → runs docker-compose, seeds demo data, opens http://localhost:5173
```
## Structure
- `ml/` Python ETL, features, models, PDF reports
- `services/api/` Spring Boot REST API
- `services/ui/` React + TypeScript dashboard
- `docs/` Documentation (architecture, data sources, modeling)
- `infra/` Postgres+PostGIS, MinIO, seed scripts
