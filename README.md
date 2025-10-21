# incremental-sales-pipeline

**🔗 Related Project**: [JP Retail Medallion Pipeline (Project A)](https://github.com/TraderKAI619/project-a-jp-retail-pipeline)
[![CI](https://github.com/TraderKAI619/incremental-sales-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/TraderKAI619/incremental-sales-pipeline/actions/workflows/ci.yml)
Idempotent **incremental** sales pipeline with **8+ data-quality checks** (pandas + DuckDB).

## ⚡ Quick Start (3 steps)
```bash
# 1) Create & activate env, then install deps
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2) One-command run (ingest → silver → gold → DQ → demo)
make run

# 3) Run tests (idempotency + data-quality)
pytest -q -k "dq or idempotency"    # or: make check
```
## 🎬 Demo（30秒）
1) **GitHub Actions** → 最新の **Success** を開く  
2) **Artifacts** → `dq-and-reports` をクリック  
3) ローカル再現：`make everything && pytest -q`

---

**📚 日本語版 README →** [README_ja.md](./README_ja.md)

---

## Data Quality (5 Layers)

Our pipeline implements comprehensive data quality checks across 5 categories:

| Category | What We Check | Implementation |
|----------|--------------|----------------|
| **Duplicates (重複)** | Natural key uniqueness: `order_date, geo_id, product_id` | `schemas/*.schema.json`, `scripts/validate_*.py`, `tests/` |
| **Missing (欠損)** | Required fields non-null/non-empty | Schema validation + quarantine logic |
| **Outliers (外れ値)** | Reasonable ranges for `quantity`, `unit_price`, `revenue_jpy` | Schema constraints + business rules |
| **Timezone (タイムゾーン)** | `order_date` normalized to JST (YYYYMMDD) | `scripts/generate_sales.py`, `scripts/to_silver.py` |
| **Schema (スキーマ)** | Column types, primary/foreign key compliance | `schemas/*.schema.json` validation |

## 🗓️ Operations / Schedule
- **Nightly**: **20:00 UTC = 05:00 JST** via GitHub Actions  
- **Artifacts**: `dq-and-reports`（`dq_report.md` / `dq_dashboard.txt` / `fact_sales.csv`）

md
## Quality Metrics
*Below values are sample metrics; for latest figures, see CI **Artifacts → `dq-and-reports`**.*
- ✅ **Pass Rate**: **≈95%（±1–2pt）**（**分母：Silver**）
- ⚠️ **Quarantine**: **≈5%**（理由は `dq_report.md` 参照）
- 📊 **Gold Output**: 例）**fact_sales ~310 rows**、returns ~11 rows
- 🎯 **Alert Threshold**: quarantine rate < 25%

> 指標は日次で更新されます。乱数シード／当日差分により ±1–2pt の自然変動があります（**分母：Silver**）。

**📊 View Latest Reports (CI Artifacts):**  
Open the latest successful workflow run → **Artifacts → `dq-and-reports`**:
- `dq_report.md` — Silver + Gold validation summary
- `dq_dashboard.txt` — Comprehensive quality dashboard
- `fact_sales.csv` — Gold fact table (sample)


```mermaid
graph TD
  subgraph Silver
    B[Data Validation<br/>5 DQ Layers]
    C[Clean Data<br/>857 records]
    D[Quarantine<br/>43 records]
  end
  subgraph Gold
    E[fact_sales<br/>310 rows]
    F[fact_returns<br/>11 rows]
  end

  A[Raw CSV Files<br/>8 days data] -->|Ingest| B
  B -->|Pass 95.2%| C
  B -->|Fail 4.8%| D
  C -->|Aggregate| E
  D -->|Extract| F

```

## Design Notes & Provenance
- Decisions (ADR-lite): see DECISIONS.md
- Quarantine examples: see data/silver/quarantine/README.md

## Tooling & Authorship

I used AI assistants for **boilerplate and documentation polish** only.
**All pipeline logic (idempotent upserts), DQ rules (5 layers), schemas, tests, and CI gates are my own work.**
Metrics in this README are reproducible from this repo’s **CI Artifacts** (see “View Latest Reports”) and
from local files under `reports/` / `data/gold/`.

---

## 🧪 Local checks
```bash
# Count rows (excluding headers)
awk 'NR>1' data/gold/fact_returns.csv | wc -l
awk 'NR>1' data/gold/fact_sales.csv   | wc -l
