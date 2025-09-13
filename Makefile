# -----------------------------
# HIRD — Makefile (repo-aligned)
# -----------------------------

# Load environment (safe if .env missing)
-include .env
export

SHELL := /bin/bash
DC    ?= docker compose

# Default tools
PYTHON ?= python
NODE   ?= npm
MVN    ?= mvn

.PHONY: help dev up down ps logs reset judge test format \
        db.up db.down db.logs db.psql db.reset \
        minio.up minio.logs smoke etl etl-crea etl-cmhc etl-statcan etl-boc etl-rentals \
        compose.check

# -----------------------------------
# Quick help
# -----------------------------------
help:
	@echo "Targets:"
	@echo "  dev              - build & run full stack (postgres, pgadmin, minio, api, ui)"
	@echo "  up               - run stack without build"
	@echo "  down             - stop all services"
	@echo "  ps               - list running services"
	@echo "  logs             - tail all service logs"
	@echo "  reset            - nuke volumes & re-create (CAUTION)"
	@echo "  db.up            - start just postgres + pgadmin"
	@echo "  db.psql          - open psql to DB (uses .env)"
	@echo "  judge            - seed demo data, then start stack"
	@echo "  test             - run ML tests, API tests, UI tests"
	@echo "  format           - ruff/black for ML; eslint fix for UI"
	@echo "  etl-*            - run individual ETL sources via daily_ingest"
	@echo "  smoke            - run minimal CREA→DB insert test"
	@echo "  compose.check    - validate docker-compose.yaml"

# -----------------------------------
# Compose orchestration
# -----------------------------------
dev: compose.check
	$(DC) up --build -d postgres pgadmin minio api ui
	$(DC) ps

up: compose.check
	$(DC) up -d postgres pgadmin minio api ui

down:
	$(DC) down

ps:
	$(DC) ps

logs:
	$(DC) logs -f

reset:
	$(DC) down -v
	$(DC) up -d postgres pgadmin

compose.check:
	@$(DC) config -q && echo "compose: OK"

# -----------------------------------
# Database helpers
# -----------------------------------
db.up:
	$(DC) up -d postgres pgadmin

db.down:
	$(DC) down

db.logs:
	docker logs -f hird-postgres

db.psql:
	@echo "Connecting to $$POSTGRES_DB at $$POSTGRES_HOST:$$POSTGRES_PORT as $$POSTGRES_USER"
	PGPASSWORD="$(POSTGRES_PASSWORD)" psql -h "$(POSTGRES_HOST)" -U "$(POSTGRES_USER)" -d "$(POSTGRES_DB)"

db.reset:
	$(DC) down -v
	$(DC) up -d postgres

# -----------------------------------
# MinIO helpers (optional)
# -----------------------------------
minio.up:
	$(DC) up -d minio

minio.logs:
	$(DC) logs -f minio

# -----------------------------------
# Seed + stack for demos
# -----------------------------------
judge:
	@bash ./infra/scripts/seed_demo.sh kelowna vancouver toronto || powershell -File ./infra/scripts/seed_demo.ps1 kelowna vancouver toronto
	$(DC) up -d

# -----------------------------------
# Tests
# -----------------------------------
test:
	@echo "Running ML tests..."
	@(cd ml && pytest -q) || true
	@echo "Running API tests..."
	@(cd services/api && $(MVN) -q -DskipITs=false test) || true
	@echo "Running UI tests..."
	@(cd services/ui && $(NODE) test) || true

# -----------------------------------
# Formatters / Linters
# -----------------------------------
format:
	@echo "Formatting ML..."
	@(cd ml && ruff check --fix . && black .) || true
	@echo "Formatting UI..."
	@(cd services/ui && $(NODE) run lint:fix) || true

# -----------------------------------
# ETL convenience targets
# -----------------------------------
etl: etl-crea etl-cmhc etl-statcan etl-boc etl-rentals

etl-crea:
	cd ml && $(PYTHON) -m pipelines.daily_ingest --source crea --date today

etl-cmhc:
	cd ml && $(PYTHON) -m pipelines.daily_ingest --source cmhc --date today

etl-statcan:
	cd ml && $(PYTHON) -m pipelines.daily_ingest --source statcan --date today

etl-boc:
	cd ml && $(PYTHON) -m pipelines.daily_ingest --source boc --date today

etl-rentals:
	cd ml && $(PYTHON) -m pipelines.daily_ingest --source rentals --date today

# -----------------------------------
# Smoke test: minimal CREA→DB insert
# -----------------------------------
smoke:
	cd ml && $(PYTHON) -m pipelines.smoke_crea_to_db

etl:
\tpython -m ml.pipelines.daily_ingest --source all --date today

etl-boc:
\tpython -m ml.pipelines.daily_ingest --source boc --date today

etl-statcan:
\tpython -m ml.pipelines.daily_ingest --source statcan --date today

etl-rentals-file:
\tpython -m ml.pipelines.daily_ingest --source rentals --date today --rentals-file=data/rentals.csv

etl-backfill-boc:
\tSTART_DATE=2010-01-01 END_DATE=2025-09-01 \\
\tpython -m ml.pipelines.daily_ingest --source boc --date 2025-09-10

# Path to migration files
MIGRATIONS_DIR = infra/db/migrations

# Use DATABASE_URL from environment
DB_URL ?= $(DATABASE_URL)

migrate:
	psql "$(DB_URL)" -f $(MIGRATIONS_DIR)/V1__etl_basics.sql
	psql "$(DB_URL)" -f $(MIGRATIONS_DIR)/V2__rent_listings_raw.sql
