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

# 一次跑完整流程
everything: ingest silver gold validate demo

# 別名
run: everything

# 產 raw（參數化）
ingest:
> $(PY) scripts/generate_sales.py --days $(GEN_DAYS) --seed $(GEN_SEED)

# raw -> silver（含隔離目錄保險建立）
silver:
> mkdir -p data/silver/quarantine
> $(PY) scripts/to_silver.py

# silver -> gold（保險建立 gold 目錄）
gold:
> mkdir -p data/gold
> $(PY) scripts/to_gold.py

# 產 DQ 報告
validate:
> mkdir -p reports
> $(PY) scripts/validate_gold.py > reports/dq_report.md

# Demo SQL（優先用 DuckDB CLI，不在就走 Python fallback）
demo:
> ( command -v duckdb >/dev/null 2>&1 && duckdb < sql/demo_queries.sql ) || $(PY) scripts/run_sql.py sql/demo_queries.sql

# 冪等性 + 測試 + quarantine 比例門檻
check:
> ./scripts/check.sh

# 清除輸出層（保留 raw）
clean:
> rm -rf data/silver/* data/gold/* reports/* || true
> mkdir -p data/silver/quarantine data/gold reports

# 清除 raw
reset:
> rm -rf data/raw/*.csv

# 偵錯：顯示變數來源
print-vars:
> @echo "GEN_DAYS='$(GEN_DAYS)' origin=$(origin GEN_DAYS)"
> @echo "GEN_SEED='$(GEN_SEED)' origin=$(origin GEN_SEED)"
