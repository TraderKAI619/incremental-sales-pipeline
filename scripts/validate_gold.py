#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pandas as pd

JST = timezone(timedelta(hours=9))
TODAY = int(datetime.now(JST).strftime("%Y%m%d"))
FACT=Path("data/gold/fact_sales.csv"); DIM=Path("data/gold/dim_date.csv")

def head():
    print("# Data Quality Report\n")
    print(f"_Generated (JST)_: **{datetime.now(JST).isoformat()}**\n")
    print("| Check | Result | Details |"); print("|---|:---:|---|")

def row(n, ok, d, warn=False):
    print(f"| {n} | {'PASS' if ok else ('WARN' if warn else 'FAIL')} | {d} |")

def last_stats(df):
    g=df.groupby("date_id").agg(rows=("order_id","count"), revenue=("revenue_jpy","sum")).reset_index()
    if g.empty: return None,None,None
    last=g.sort_values("date_id").iloc[-1]
    prev=g.sort_values("date_id").iloc[:-1].tail(7)
    return last, prev, g

def main():
    head()
    if not FACT.exists(): print("**FAIL** no fact."); return
    df=pd.read_csv(FACT)
    for c in ["quantity","unit_price","revenue_jpy"]:
        if c in df.columns: df[c]=pd.to_numeric(df[c],errors="coerce")

    need=["order_id","date_id","geo_id","product_id","quantity","unit_price","revenue_jpy","updated_at"]
    miss=[c for c in need if c not in df.columns]; row("Required Columns", len(miss)==0, f"missing={miss}" if miss else "all present")
    row("Primary Key Unique", not df["order_id"].duplicated().any(), f"duplicates={int(df['order_id'].duplicated().sum())}")
    keys=["order_id","date_id","geo_id"]; nulls={k:int(df[k].isna().sum()) for k in keys if k in df.columns}
    row("No Nulls in Keys", all(v==0 for v in nulls.values()), f"nulls={nulls}")
    ok4=(df["quantity"]>0).all() and (df["unit_price"]>0).all() and (df["unit_price"]<=100000).all() and (df["revenue_jpy"]>=0).all()
    row("Numeric Ranges", bool(ok4), f"min_qty={df['quantity'].min()}, max_price={df['unit_price'].max():.2f}")
    di=pd.to_numeric(df["date_id"],errors="coerce").astype("Int64")
    two=int((datetime.now(JST)-timedelta(days=730)).strftime("%Y%m%d"))
    row("Date Range", bool(di.notna().all() and (di<=TODAY).all() and (di>=two).all()),
        f"range=({int(di.min())}..{int(di.max())})")
    dim=pd.read_csv(DIM) if DIM.exists() else pd.DataFrame({"date_id":[]})
    miss_fk=set(di.dropna().astype(int)) - set(pd.to_numeric(dim["date_id"],errors="coerce").dropna().astype(int))
    row("FK: date_id in dim_date", len(miss_fk)==0, f"missing_in_dim={list(sorted(miss_fk))[:5]}{'...' if len(miss_fk)>5 else ''}")
    last, prev, _ = last_stats(df)
    if prev is None or prev.empty or len(prev)<3:
        row("Daily Volume Anomaly", True, "insufficient history (<3 days) -> WARN", warn=True)
        row("Daily Revenue Spike", True, "insufficient history (<3 days) -> WARN", warn=True)
    else:
        med=prev["rows"].median(); dev=abs(int(last["rows"])-med)/(med if med else 1)
        row("Daily Volume Anomaly", dev<=0.60, f"last={int(last['rows'])}, median7={int(med)}, deviation={dev:.2%}")
        medr=prev["revenue"].median(); ratio=(last["revenue"]/medr) if medr else float("inf")
        row("Daily Revenue Spike", ratio<=2.5, f"last={last['revenue']:.2f}, median7={medr:.2f}, ratio={ratio:.2f}x")
    row("Non-negative Totals", (df["quantity"].sum()>=0) and (df["revenue_jpy"].sum()>=0),
        f"sum_qty={int(df['quantity'].sum())}, sum_rev={df['revenue_jpy'].sum():.2f}")
    diff=(df["revenue_jpy"] - df["quantity"]*df["unit_price"]).abs()
    row("Revenue Consistency", (diff<=0.01).all(), f"max_abs_diff={diff.max():.4f}")

if __name__=="__main__":
    main()
