#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import pandas as pd

SILVER = Path("data/silver")
GOLD = Path("data/gold"); GOLD.mkdir(parents=True, exist_ok=True)
FACT = GOLD/"fact_sales.csv"
DIM  = GOLD/"dim_date.csv"

def build_dim_date(start="2024-01-01", end="2025-12-31"):
    if DIM.exists(): return
    d = pd.date_range(start, end, freq="D")
    pd.DataFrame({"date_id": d.strftime("%Y%m%d").astype(int), "date": d.strftime("%Y-%m-%d")}) \
      .to_csv(DIM, index=False, encoding="utf-8", lineterminator="\n")
    print(f"Wrote {DIM}")

def read_new():
    frames=[]
    for p in sorted(SILVER.glob("sales_clean_*.csv")):
        df=pd.read_csv(p)
        df["date_id"]=pd.to_numeric(df["order_date"], errors="coerce").astype("Int64")
        df["updated_at"]=df["processed_at"]
        frames.append(df[["order_id","date_id","geo_id","product_id","quantity","unit_price","revenue_jpy","updated_at"]])
    return pd.concat(frames, ignore_index=True) if frames else \
        pd.DataFrame(columns=["order_id","date_id","geo_id","product_id","quantity","unit_price","revenue_jpy","updated_at"])

def upsert(df_new):
    if df_new.empty: return
    df_new["quantity"]=pd.to_numeric(df_new["quantity"], errors="coerce").fillna(0).astype(int)
    df_new["unit_price"]=pd.to_numeric(df_new["unit_price"], errors="coerce").fillna(0.0)
    df_new["revenue_jpy"]=pd.to_numeric(df_new["revenue_jpy"], errors="coerce").fillna(0.0)

    if FACT.exists():
        old=pd.read_csv(FACT)
        old=old[~old["order_id"].isin(set(df_new["order_id"]))].copy()
        comb=pd.concat([old, df_new], ignore_index=True)
    else:
        comb=df_new.copy()

    comb=comb.sort_values(by=["order_id"], kind="mergesort").reset_index(drop=True)
    comb.to_csv(FACT, index=False, encoding="utf-8", lineterminator="\n")
    print(f"Wrote {FACT} rows={len(comb)}")

def main():
    build_dim_date()
    upsert(read_new())

if __name__=="__main__":
    main()
