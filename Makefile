.RECIPEPREFIX := >
SHELL := /bin/bash
PY := python

.PHONY: help ingest silver gold validate demo everything clean run check

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
> @echo "  run       - alias for everything"

everything: ingest silver gold validate demo

run: everything

ingest:
> $(PY) scripts/generate_sales.py --days 7 --seed 42

silver:
> $(PY) scripts/to_silver.py

gold:
> $(PY) scripts/to_gold.py

validate:
> @mkdir -p reports
> $(PY) scripts/validate_gold.py > reports/dq_report.md

demo:
> ( command -v duckdb >/dev/null 2>&1 && duckdb < sql/demo_queries.sql ) || $(PY) scripts/run_sql.py sql/demo_queries.sql

check: everything
check:
> bash -eu -o pipefail -c '\
  echo "== Idempotency =="; \
  # 確保先有 gold 檔（第一次跑 CI 時很重要）
  test -f data/gold/fact_sales.csv || { echo "(no gold yet) running make gold..."; $(PY) scripts/to_gold.py >/dev/null; }; \
  r1=$$(($$(wc -l < data/gold/fact_sales.csv)-1)); \
  $(PY) scripts/to_gold.py >/dev/null; \
  r2=$$(($$(wc -l < data/gold/fact_sales.csv)-1)); \
  test "$$r1" = "$$r2" && echo "  ✅ idempotent (rows=$$r2)" || { echo "  ❌ not idempotent (before=$$r1 after=$$r2)"; exit 1; }; \
  echo; echo "== Tests =="; pytest -q tests/ || exit 1; \
  echo; echo "== Quarantine < 25% =="; \
  bad=0; shopt -s nullglob; \
  for f in data/silver/quarantine/*.csv; do n=$$(($$(wc -l < "$$f")-1)); (( n>0 )) && bad=$$((bad+n)); done; \
  gold=$$(($$(wc -l < data/gold/fact_sales.csv)-1)); \
  total=$$((gold+bad)); pct=$$(awk -v b="$$bad" -v t="$$total" '\''BEGIN{ if(t==0){print 0}else{ printf "%.1f",(b/t)*100 }}'\''); \
  echo "  bad=$$bad, gold=$$gold, total=$$total, pct=$${pct}%"; \
  awk -v p="$$pct" '\''BEGIN{ exit (p<25.0)?0:1 }'\'' \
    && echo "  ✅ OK" \
    || { echo "  ❌ too high"; exit 1; } \
'

clean:
> rm -rf data/silver/* data/gold/* reports/* || true
> mkdir -p data/silver/quarantine data/gold reports

check:
> scripts/check.sh
