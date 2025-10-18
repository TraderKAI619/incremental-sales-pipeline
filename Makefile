.DEFAULT_GOAL := everything
.DELETE_ON_ERROR:
.RECIPEPREFIX := >

SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
MAKEFLAGS += --warn-undefined-variables

# ===== 變數區 =====
PY        := python3
GEN_DAYS ?= 7
GEN_SEED ?= 42

.PHONY: help ingest silver gold validate demo everything clean run check reset print-vars

help:
> @echo "Targets:"
> @echo "  ingest     - generate raw sample data (days=$(GEN_DAYS), seed=$(GEN_SEED))"
> @echo "  silver     - clean & quarantine, compute revenue_jpy"
> @echo "  gold       - idempotent upsert -> data/gold/fact_sales.csv"
> @echo "  validate   - 10 DQ checks -> reports/dq_report.md"
> @echo "  demo       - run demo SQL (DuckDB CLI or Python fallback)"
> @echo "  check      - idempotency + tests + quarantine gate"
> @echo "  everything - ingest -> silver -> gold -> validate -> demo"
> @echo "  clean      - remove outputs"
> @echo "  reset      - remove raw inputs"
> @echo "  run        - alias for everything"
> @echo ""
> @echo "Variables (override with make VAR=...):"
> @echo "  GEN_DAYS=$(GEN_DAYS)  GEN_SEED=$(GEN_SEED)  PY=$(PY)"

everything: ingest silver gold validate demo
run: everything

ingest:
> $(PY) scripts/generate_sales.py --days $(GEN_DAYS) --seed $(GEN_SEED)

silver:
> mkdir -p data/silver/quarantine
> $(PY) scripts/to_silver.py

gold:
> mkdir -p data/gold
> $(PY) scripts/to_gold.py

validate:
> mkdir -p reports
> $(PY) scripts/validate_gold.py > reports/dq_report.md

demo:
> ( command -v duckdb >/dev/null 2>&1 && duckdb < sql/demo_queries.sql ) || $(PY) scripts/run_sql.py sql/demo_queries.sql

check:
> ./scripts/check.sh

clean:
> rm -rf data/silver/* data/gold/* reports/* || true
> mkdir -p data/silver/quarantine data/gold reports

reset:
> rm -rf data/raw/*.csv

print-vars:
> @echo "GEN_DAYS='$(GEN_DAYS)' origin=$(origin GEN_DAYS)"
> @echo "GEN_SEED='$(GEN_SEED)' origin=$(origin GEN_SEED)"
