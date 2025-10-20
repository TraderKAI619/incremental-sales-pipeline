.DEFAULT_GOAL := everything
.DELETE_ON_ERROR:
.RECIPEPREFIX := >
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
MAKEFLAGS += --warn-undefined-variables

# ===== variables =====
PY        := python3
GEN_DAYS ?= 7
GEN_SEED ?= 42

.PHONY: help ingest silver gold validate demo everything clean run check reset returns dashboard trends

help:

# Main pipeline flow
everything: ingest silver gold validate demo

run: everything

# Individual stages
ingest:
> $(PY) scripts/generate_sales.py --days $(GEN_DAYS) --seed $(GEN_SEED)

silver: ingest
> mkdir -p data/silver/quarantine
> $(PY) scripts/to_silver.py

gold: silver
> mkdir -p data/gold
> $(PY) scripts/to_gold.py

# Validation - NO RECURSIVE CALLS!
validate: gold
> mkdir -p reports
> $(PY) scripts/validate_silver.py || true
> $(PY) scripts/validate_gold.py

demo: gold
> ( command -v duckdb >/dev/null 2>&1 && duckdb < sql/demo_queries.sql ) || $(PY) scripts/run_sql.py sql/demo_queries.sql

check: silver
> ./scripts/check.sh

# Monitoring targets
# Generate comprehensive dashboard
# Cleanup
clean:
> rm -rf data/silver/* data/gold/* reports/* || true
> mkdir -p data/silver/quarantine data/gold reports

reset:
> rm -rf data/raw/*.csv

dashboard: validate
> $(PY) scripts/dq_dashboard.py > reports/dq_dashboard.txt

# Extract returns/adjustments analysis
returns: gold
> $(PY) -c "import pandas as pd, glob; \
>   df = pd.concat([pd.read_csv(f) for f in glob.glob('data/silver/quarantine/*.csv')]); \
>   returns = df[df['_bad_reason'].str.contains('neg_or_zero_qty')]; \
>   returns.to_csv('data/gold/fact_returns.csv', index=False); \
>   print(f'Extracted {len(returns)} potential returns')"

# Update quarantine trend tracking
trends: validate
> $(PY) scripts/update_trends.py
> @echo "✅ Trends updated in reports/quarantine_trends.csv"




.PHONY: readme-check
readme-check:
> @bash scripts/suggest_readme_updates.sh || true
