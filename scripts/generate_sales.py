#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate raw daily sales CSVs for N days with fixed randomness.
- data/raw/sales_YYYYMMDD.csv
- columns: order_id, order_date, geo_id, product_id, quantity, unit_price
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd

JST = ZoneInfo("Asia/Tokyo")
GEO_POOL = ["GEO01","GEO02","GEO03","GEO04","GEO05"]
PRODUCT_POOL = [f"P{i:03d}" for i in range(1,9)]

def ymd(dt): return dt.strftime("%Y%m%d")

def gen_one_day(rng, d):
    n = int(rng.integers(80, 141))
    df = pd.DataFrame({
        "order_id": [f"{ymd(d)}-{i:04d}" for i in range(n)],
        "order_date": ymd(d),
        "geo_id": rng.choice(GEO_POOL, n),
        "product_id": rng.choice(PRODUCT_POOL, n),
        "quantity": rng.integers(1, 6, n),
        "unit_price": rng.choice([100,150,200,250,300,500,800,1000], n).astype(float),
    })
    # ~2% 重複
    dup = max(1, int(round(n*0.02)))
    df = pd.concat([df, df.sample(dup, random_state=int(rng.integers(0,2**31)))], ignore_index=True)
    # ~5% 壞列
    badc = max(1, int(round(len(df)*0.05)))
    bad=[]
    for i in range(badc):
        kind = rng.choice(["neg_qty","zero_price","missing_geo","bad_date"])
        row = {
            "order_id": f"{ymd(d)}-BAD{i:03d}",
            "order_date": ymd(d),
            "geo_id": rng.choice(GEO_POOL),
            "product_id": rng.choice(PRODUCT_POOL),
            "quantity": int(rng.integers(1,6)),
            "unit_price": float(rng.choice([100,150,200,250,300,500,800,1000])),
        }
        if kind=="neg_qty": row["quantity"] = -int(rng.integers(1,5))
        elif kind=="zero_price": row["unit_price"] = 0.0
        elif kind=="missing_geo": row["geo_id"] = ""
        elif kind=="bad_date": row["order_date"] = f"2025{rng.integers(13,20)}{rng.integers(32,40)}"
        bad.append(row)
    df = pd.concat([df, pd.DataFrame(bad)], ignore_index=True)
    return df.sample(frac=1.0, random_state=int(rng.integers(0,2**31))).reset_index(drop=True)[
        ["order_id","order_date","geo_id","product_id","quantity","unit_price"]
    ]

def main():
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--seed", type=int, default=42)
    a=ap.parse_args()
    rng=np.random.default_rng(a.seed)
    out=Path("data/raw"); out.mkdir(parents=True, exist_ok=True)
    today=datetime.now(JST).replace(tzinfo=None); start=today - timedelta(days=a.days-1)
    for i in range(a.days):
        d = start + timedelta(days=i)
        fn = out / f"sales_{ymd(d)}.csv"
        gen_one_day(rng, d).to_csv(fn, index=False, encoding="utf-8", lineterminator="\n")
        print(f"Wrote {fn}")
if __name__=="__main__": main()
