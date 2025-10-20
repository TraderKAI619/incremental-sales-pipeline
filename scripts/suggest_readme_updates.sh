#!/usr/bin/env bash
set -euo pipefail

echo "📊 README Update Checklist"
echo "=========================="
echo "Current date: $(TZ=Asia/Tokyo date +%F)"
echo

pass="" quar="" good="" bad="" total=""

# 1) 優先嘗試：從 reports/dq_dashboard.txt 擷取
if [[ -f reports/dq_dashboard.txt ]]; then
  # 嘗試抓 "Totals -> good=..., bad=..." 或一般 good=/bad= 形式
  totals=$(grep -E 'Totals[^0-9]*good=.*bad=|good=[0-9]+.*bad=[0-9]+' reports/dq_dashboard.txt | tail -1 || true)
  if [[ -n "${totals:-}" ]]; then
    good=$(echo "$totals" | grep -Eo 'good=[0-9]+' | tail -1 | cut -d= -f2)
    bad=$( echo "$totals" | grep -Eo 'bad=[0-9]+'  | tail -1 | cut -d= -f2)
  fi
fi

# 2) 後備方案：直接統計檔案（最可靠）
if [[ -z "${good:-}" || -z "${bad:-}" ]]; then
  # good = 所有 data/silver/sales_clean_*.csv 的總列數扣掉每檔 1 行表頭
  if ls data/silver/sales_clean_*.csv >/dev/null 2>&1; then
    good=$(awk 'FNR>1{g++} END{print g+0}' data/silver/sales_clean_*.csv)
  else
    good=0
  fi
  # bad = quarantine/*.csv 的總列數扣掉每檔 1 行表頭（無檔時為 0）
  if ls data/silver/quarantine/*.csv >/dev/null 2>&1; then
    bad=$(awk 'FNR>1{b++} END{print b+0}' data/silver/quarantine/*.csv)
  else
    bad=0
  fi
fi

total=$(( good + bad ))

echo "Quality Metrics:"
if [[ "$total" -gt 0 ]]; then
  pass=$(awk -v g="$good" -v t="$total" 'BEGIN{printf "%.1f%%",(g/t)*100}')
  quar=$(awk -v b="$bad"  -v t="$total" 'BEGIN{printf "%.1f%%",(b/t)*100}')
  echo "  - Pass Rate: $pass ($good/$total)"
  echo "  - Quarantine: $quar ($bad)"
else
  echo "  - (No rows found; run: make dashboard)"
fi
echo

# Gold/Returns 行數（不含表頭）
if [[ -f data/gold/fact_sales.csv ]]; then
  sales_rows=$(awk 'NR>1' data/gold/fact_sales.csv   | wc -l)
  echo "Gold tables:"
  echo "  - fact_sales:   $sales_rows rows"
fi
if [[ -f data/gold/fact_returns.csv ]]; then
  returns_rows=$(awk 'NR>1' data/gold/fact_returns.csv | wc -l)
  echo "  - fact_returns: $returns_rows rows"
fi
echo

echo "📝 Update in README.md:"
echo "  1) Quality Metrics (Last run: today)"
echo "  2) Pass/Quarantine numbers & Gold Output"
echo "  3) Mermaid labels (Clean/Quarantine/Gold rows + Pass/Fail %)"
echo "  4) Performance Snapshot if you re-ran benchmarks"
