.PHONY: dev judge test format

dev:
	docker-compose up --build

judge:
	bash ./infra/scripts/seed_demo.sh kelowna vancouver toronto || powershell -File ./infra/scripts/seed_demo.ps1 kelowna vancouver toronto
	docker-compose up -d --build

test:
	(cd ml && pytest -q) || true
	(cd services/api && mvn -q -DskipITs=false test) || true
	(cd services/ui && npm test) || true

format:
	(cd ml && ruff check --fix . && black .) || true
	(cd services/ui && npm run lint:fix) || true

# --- ETL convenience targets ---
etl: etl-crea etl-cmhc etl-statcan etl-boc

etl-crea:
\tcd ml && python -m pipelines.daily_ingest --source crea --date today

etl-cmhc:
\tcd ml && python -m pipelines.daily_ingest --source cmhc --date today

etl-statcan:
\tcd ml && python -m pipelines.daily_ingest --source statcan --date today

etl-boc:
\tcd ml && python -m pipelines.daily_ingest --source boc --date today

