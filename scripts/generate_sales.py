#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate raw daily sales CSVs for N days with fixed randomness.
- Output: data/raw/sales_YYYYMMDD.csv
- Columns: order_id, order_date, geo_id, product_id, quantity, unit_price
- Per day: 80~140 rows, ~2% duplicate order_id, ~5% bad rows
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd

JST = ZoneInfo("Asia/Tokyo")

# smaller pools → 更快、更好看
GEO_POOL = ["GEO01","GEO02","GEO03","GEO04","GEO05"]
PRODUCT_POOL = [f"P{i:03d}" for i in range(1,9)]  # 8 種

def ymd(dt: datetime) -> str:
    return dt.strftime("%Y%m%d")

def gen_one_day(rng: np.random.Generator, the_date: datetime) -> pd.DataFrame:
    n = int(rng.integers(80, 141))  # 80~140
    base_ids = [f"{ymd(the_date)}-{i:04d}" for i in range(n)]
    df = pd.DataFrame({
        "order_id": base_ids,
        "order_date": ymd(the_date),
        "geo_id": rng.choice(GEO_POOL, size=n),
        "product_id": rng.choice(PRODUCT_POOL, size=n),
        "quantity": rng.integers(1, 6, size=n),                 # 1..5
        "unit_price": rng.choice([100,150,200,250,300,500,800,1000], size=n).astype(float),
    })

    # ~2% duplicate order_id（完整複製列）
    dup_count = max(1, int(round(n * 0.02)))
    dup_rows = df.sample(n=dup_count, random_state=int(rng.integers(0, 2**31)), replace=False)
    df = pd.concat([df, dup_rows], ignore_index=True)

    # ~5% bad rows
    bad_count = max(1, int(round(len(df) * 0.05)))
    bad_rows = []
    for i in range(bad_count):
        kind = rng.choice(["neg_qty","zero_price","missing_geo","bad_date"])
        row = {
            "order_id": f"{ymd(the_date)}-BAD{i:03d}",
            "order_date": ymd(the_date),
            "geo_id": rng.choice(GEO_POOL),
            "product_id": rng.choice(PRODUCT_POOL),
            "quantity": int(rng.integers(1,6)),
            "unit_price": float(rng.choice([100,150,200,250,300,500,800,1000])),
        }
        if kind == "neg_qty":
            row["quantity"] = -int(rng.integers(1,5))
        elif kind == "zero_price":
            row["unit_price"] = 0.0
        elif kind == "missing_geo":
            row["geo_id"] = ""
        elif kind == "bad_date":
            row["order_date"] = f"2025{rng.integers(13,20)}{rng.integers(32,40)}"
        bad_rows.append(row)
    df = pd.concat([df, pd.DataFrame(bad_rows)], ignore_index=True)

    # 洗牌但保持種子穩定
    df = df.sample(frac=1.0, random_state=int(rng.integers(0, 2**31))).reset_index(drop=True)
    df = df[["order_id","order_date","geo_id","product_id","quantity","unit_price"]]
    return df

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    out_dir = Path("data/raw"); out_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now(JST).replace(tzinfo=None)
    start = today - timedelta(days=args.days - 1)
    for i in range(args.days):
        d = start + timedelta(days=i)
        fn = out_dir / f"sales_{ymd(d)}.csv"
        gen_one_day(rng, d).to_csv(fn, index=False, encoding="utf-8", lineterminator="\n")
        print(f"Wrote {fn}")
    print("Done.")

if __name__ == "__main__":
    main()
