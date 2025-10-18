#!/usr/bin/env bash
set -euo pipefail

echo "== Idempotency =="
[[ -f data/gold/fact_sales.csv ]] || python scripts/to_gold.py >/dev/null
r1=$(( $(wc -l < data/gold/fact_sales.csv) - 1 ))
python scripts/to_gold.py >/dev/null
r2=$(( $(wc -l < data/gold/fact_sales.csv) - 1 ))
if [[ "$r1" == "$r2" ]]; then
  echo "  ✅ idempotent (rows=$r2)"
else
  echo "  ❌ not idempotent (before=$r1 after=$r2)"; exit 1
fi

echo; echo "== Tests =="
pytest -q tests/

echo; echo "== Quarantine < 25% =="
bad=0; shopt -s nullglob
for f in data/silver/quarantine/*.csv; do
  n=$(( $(wc -l < "$f") - 1 ))
  (( n>0 )) && bad=$((bad+n))
done
gold=$(( $(wc -l < data/gold/fact_sales.csv) - 1 ))
total=$((gold+bad))
pct=$(awk -v b="$bad" -v t="$total" 'BEGIN{ if(t==0){print 0}else{ printf "%.1f",(b/t)*100 }}')
echo "  bad=$bad, gold=$gold, total=$total, pct=${pct}%"
awk -v p="$pct" 'BEGIN{ exit (p<25.0)?0:1 }' \
  && echo "  ✅ OK" \
  || { echo "  ❌ too high"; exit 1; }
