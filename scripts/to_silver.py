#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
from pathlib import Path
import pandas as pd
from datetime import datetime

RAW = Path("data/raw")
SILVER = Path("data/silver"); QUAR = SILVER/"quarantine"
SILVER.mkdir(parents=True, exist_ok=True); QUAR.mkdir(parents=True, exist_ok=True)
F = re.compile(r"sales_(\d{8})\.csv$")

def parse_date8(s): 
    try: datetime.strptime(str(s), "%Y%m%d"); return True
    except: return False

def clean_one(day, df):
    need = ["order_id","order_date","geo_id","product_id","quantity","unit_price"]
    for c in need:
        if c not in df.columns: df[c]=pd.NA
    df = df.drop_duplicates().copy()

    reasons=[]
    for _,r in df.iterrows():
        bad=[]
        if not parse_date8(r["order_date"]): bad.append("bad_date")
        if pd.isna(r["geo_id"]) or str(r["geo_id"]).strip()=="": bad.append("missing_geo")
        try: q=float(r["quantity"])
        except: q=-1
        try: p=float(r["unit_price"])
        except: p=-1
        if q<=0: bad.append("neg_or_zero_qty")
        if p<=0: bad.append("neg_or_zero_price")
        reasons.append(",".join(bad))
    df["_bad_reason"]=reasons
    bad_mask=df["_bad_reason"].str.len()>0
    bad=df.loc[bad_mask].copy(); good=df.loc[~bad_mask].copy()

    if not bad.empty:
        bad["source_file"]=f"sales_{day}.csv"
        bad.to_csv(QUAR/f"sales_bad_{day}.csv", index=False, encoding="utf-8", lineterminator="\n")

    good = good.drop_duplicates(subset=["order_id"], keep="first").copy()
    good["quantity"]=pd.to_numeric(good["quantity"], errors="coerce").fillna(0).astype(int)
    good["unit_price"]=pd.to_numeric(good["unit_price"], errors="coerce").fillna(0.0)
    good["revenue_jpy"]=good["quantity"]*good["unit_price"]
    good["processed_at"]=day
    cols=["order_id","order_date","geo_id","product_id","quantity","unit_price","revenue_jpy","processed_at"]
    out=SILVER/f"sales_clean_{day}.csv"
    good[cols].to_csv(out, index=False, encoding="utf-8", lineterminator="\n")
    return len(good), len(bad)

def main():
    total_g=total_b=0; anyf=False
    for p in sorted(RAW.glob("sales_*.csv")):
        m=F.search(p.name); 
        if not m: continue
        anyf=True
        day=m.group(1); df=pd.read_csv(p, dtype=str)
        g,b=clean_one(day, df)
        print(f"Processed {p.name}: good={g}, bad={b}")
        total_g+=g; total_b+=b
    print("No raw files found." if not anyf else f"Totals -> good={total_g}, bad={total_b}")

if __name__=="__main__":
    main()
