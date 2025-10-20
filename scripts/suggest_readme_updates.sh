#!/usr/bin/env bash
set -euo pipefail

echo "📊 README Update Checklist"
echo "=========================="
echo "Current date: $(TZ=Asia/Tokyo date +%F)"
echo

if [[ -f reports/dq_dashboard.txt ]]; then
  echo "Quality Metrics (from reports/dq_dashboard.txt):"
  line=$(grep -E 'good=|bad=' reports/dq_dashboard.txt | head -1 || true)
  if [[ -n "${line:-}" ]]; then
    good=$(echo "$line" | grep -Eo 'good=[0-9]+' | cut -d= -f2)
    bad=$(echo "$line"  | grep -Eo 'bad=[0-9]+'  | cut -d= -f2)
    total=$(( ${good:-0} + ${bad:-0} ))
    if [[ ${total:-0} -gt 0 ]]; then
      pass=$(awk -v g="$good" -v t="$total" 'BEGIN{printf "%.1f%%",(g/t)*100}')
      quar=$(awk -v b="$bad" -v t="$total" 'BEGIN{printf "%.1f%%",(b/t)*100}')
      echo "  - Pass Rate: $pass ($good/$total)"
      echo "  - Quarantine: $quar ($bad)"
    else
      echo "  - (Totals not found)"
    fi
  else
    echo "  - (No metrics line found)"
  fi
  echo
fi

if [[ -f data/gold/fact_sales.csv ]]; then
  sales_rows=$(wc -l < data/gold/fact_sales.csv)
  echo "Gold tables (incl. header):"
  echo "  - fact_sales:  $sales_rows rows"
fi
if [[ -f data/gold/fact_returns.csv ]]; then
  returns_rows=$(wc -l < data/gold/fact_returns.csv)
  echo "  - fact_returns: $returns_rows rows"
fi
echo

echo "📝 Update in README.md:"
echo "  1) Quality Metrics date (Last run: YYYY-MM-DD)"
echo "  2) Pass/Quarantine numbers & Gold Output"
echo "  3) Mermaid labels (Clean/Quarantine/Gold rows + Pass/Fail %)"
echo "  4) Performance Snapshot if benchmarks re-ran"
