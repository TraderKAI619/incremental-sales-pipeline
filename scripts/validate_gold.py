# scripts/validate_gold.py
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
from validate_utils import load_schema, validate_df, write_markdown

def main():
    gold = Path("data/gold/fact_sales.csv")
    if not gold.exists():
        print("Gold not found: data/gold/fact_sales.csv", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(gold)
    schema = load_schema("schemas/fact_sales_gold.schema.json")
    rep = validate_df(df, schema)

    ok = (len(rep["errors"]) == 0)
    summary = {
        "gold_rows": rep["counts"].get("rows", 0),
        "pk_duplicates": rep.get("pk_duplicates", 0),
        "errors": 0 if ok else len(rep["errors"])
    }
    if not ok:
        summary["error_samples"] = rep["errors"][:10]

    write_markdown("reports/dq_report.md", "Data Quality Report (Gold)", summary)
    print(summary)
    sys.exit(0 if ok else 2)

if __name__ == "__main__":
    main()
