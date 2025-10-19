# scripts/validate_silver.py
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
from validate_utils import load_schema, validate_df, write_markdown

def main():
    silver_dir = Path("data/silver")
    files = sorted(silver_dir.glob("sales_clean_*.csv"))
    if not files:
        print("No silver files found.", file=sys.stderr)
        sys.exit(1)

    schema = load_schema("schemas/sales_silver.schema.json")

    total_rows = 0
    all_errors = []
    for f in files:
        df = pd.read_csv(f)
        rep = validate_df(df, schema)
        total_rows += len(df)
        if rep["errors"]:
            all_errors.append(f"{f.name}: " + "; ".join(rep["errors"]))

    ok = (len(all_errors) == 0)
    summary = {
        "silver_files": len(files),
        "silver_rows_total": total_rows,
        "silver_errors": 0 if ok else len(all_errors)
    }
    if not ok:
        summary["error_samples"] = all_errors[:10]

    write_markdown("reports/dq_report.md", "Data Quality Report (Silver)", summary)
    print(summary)
    sys.exit(0 if ok else 2)

if __name__ == "__main__":
    main()
