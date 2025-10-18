.DEFAULT_GOAL := everything
.RECIPEPREFIX := >
SHELL := /bin/bash
PY := python3

.PHONY: help ingest silver gold validate demo everything clean run check reset

reset:
> rm -rf data/raw/*.csv

help:
> @echo "Targets:"
> @echo "  ingest    - generate raw sample data (fixed seed)"
> @echo "  silver    - clean & quarantine, compute revenue_jpy"
> @echo "  gold      - idempotent upsert -> data/gold/fact_sales.csv"
> @echo "  validate  - 10 DQ checks -> reports/dq_report.md"
> @echo "  demo      - run demo SQL (DuckDB CLI or Python fallback)"
> @echo "  check     - idempotency + tests + quarantine gate"
> @echo "  everything- ingest -> silver -> gold -> validate -> demo"
> @echo "  clean     - remove outputs"
> @echo "  reset     - remove raw inputs"
> @echo "  run       - alias for everything"

everything: ingest silver gold validate demo

run: everything

ingest:
> $(PY) scripts/generate_sales.py --days 7 --seed 42

silver:
> mkdir -p data/silver/quarantine
> $(PY) scripts/to_silver.py

gold:
> mkdir -p data/gold
> $(PY) scripts/to_gold.py

validate:
> @mkdir -p reports
> $(PY) scripts/validate_gold.py > reports/dq_report.md

demo:
> ( command -v duckdb >/dev/null 2>&1 && duckdb < sql/demo_queries.sql ) || $(PY) scripts/run_sql.py sql/demo_queries.sql

check:
> ./scripts/check.sh

clean:
> rm -rf data/silver/* data/gold/* reports/* || true
> mkdir -p data/silver/quarantine data/gold reports
print-vars:
> @echo "DAYS='$(DAYS)' origin=$(origin DAYS)"
> @echo "SEED='$(SEED)' origin=$(origin SEED)"
