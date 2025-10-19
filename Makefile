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
> $(PY) scripts/validate_silver.py || true
> $(PY) scripts/validate_gold.py

> @$(MAKE) run
> $(PY) scripts/validate_silver.py || true
> $(PY) scripts/validate_gold.py
> pytest -q

> rm -rf data/silver/* data/gold/* reports/* || true
> mkdir -p data/silver/quarantine data/gold reports

reset:
> rm -rf data/raw/*.csv

print-vars:
> @echo "GEN_DAYS='$(GEN_DAYS)' origin=$(origin GEN_DAYS)"
> @echo "GEN_SEED='$(GEN_SEED)' origin=$(origin GEN_SEED)"

returns: gold
> @echo "Extracting returns/adjustments..."
> python3 -c "import pandas as pd, glob; \
>   df = pd.concat([pd.read_csv(f) for f in glob.glob('data/silver/quarantine/*.csv')]); \
>   returns = df[df['_bad_reason'].str.contains('neg_or_zero_qty')]; \
>   returns.to_csv('data/gold/fact_returns.csv', index=False); \
>   print(f'Extracted {len(returns)} potential returns')"


dashboard: validate
> python3 scripts/dq_dashboard.py

trends: validate
> python3 scripts/update_trends.py

