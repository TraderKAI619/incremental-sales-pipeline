import os, glob
import pandas as pd

SILVER_DIR = "data/silver"
GOLD_PATH = "data/gold/fact_sales.csv"

# 自然鍵候選（加入 date_id + geo_id 組合）
NATURAL_KEY_CANDIDATES = [
    ["date_id", "geo_id", "product_id"],      # ← 你的實際 schema
    ["date", "store_id", "product_id"],
    ["order_date", "store_id", "product_id"],
    ["date", "store_id", "sku"],
    ["ts", "store_id", "product_id"],
    ["yyyymmdd", "store_id", "product_id"],
]

def pick_natural_key(cols):
    lower = {c.lower(): c for c in cols}
    for cand in NATURAL_KEY_CANDIDATES:
        if all(k in lower for k in (c.lower() for c in cand)):
            return [lower[c.lower()] for c in cand]
    return None

def read_silver_df():
    candidates = [
        os.path.join(SILVER_DIR, "fact_sales_clean.csv"),
        os.path.join(SILVER_DIR, "fact_sales.csv"),
    ]
    paths = [p for p in candidates if os.path.exists(p)]
    if not paths:
        paths = [p for p in glob.glob(os.path.join(SILVER_DIR, "*.csv")) if "quarantine" not in p]
    if not paths:
        raise SystemExit("No silver CSV found under data/silver/")
    dfs = [pd.read_csv(p) for p in paths]
    return pd.concat(dfs, ignore_index=True)

def ensure_revenue(df: pd.DataFrame) -> pd.DataFrame:
    lowers = {c.lower(): c for c in df.columns}
    if "revenue_jpy" in lowers:
        return df
    ucol = lowers.get("units") or lowers.get("quantity")
    pcol = lowers.get("unit_price") or lowers.get("price_jpy") or lowers.get("price")
    if ucol and pcol:
        df["revenue_jpy"] = df[ucol].fillna(0) * df[pcol].fillna(0)
        return df
    raise SystemExit(
        "Cannot calculate revenue_jpy. Expected either:\n"
        "  - column 'revenue_jpy', or\n"
        "  - both ('units'|'quantity') AND ('unit_price'|'price_jpy'|'price')\n"
        f"Found columns: {list(df.columns)}"
    )

def make_nk_series(df: pd.DataFrame, key_cols):
    parts = [df[c].astype("string").fillna("") for c in key_cols]
    out = parts[0]
    for p in parts[1:]:
        out = out.str.cat(p, sep="|")
    return out

def sort_by_date_if_possible(df: pd.DataFrame) -> pd.DataFrame:
    lowers = {c.lower(): c for c in df.columns}
    # 加入 date_id, updated_at
    for cand in ("date", "order_date", "date_id", "updated_at", "ts", "yyyymmdd"):
        if cand in lowers:
            col = lowers[cand]
            try:
                if cand in ("yyyymmdd", "date_id", "updated_at"):
                    s = pd.to_datetime(df[col].astype("string"), format="%Y%m%d", errors="coerce")
                elif cand == "ts" and pd.api.types.is_numeric_dtype(df[col]):
                    unit = "ms" if pd.to_numeric(df[col], errors="coerce").max() > 1e12 else "s"
                    s = pd.to_datetime(df[col], unit=unit, errors="coerce")
                else:
                    s = pd.to_datetime(df[col], errors="coerce")
                df = df.assign(_sort=s).sort_values("_sort", kind="stable").drop(columns=["_sort"])
                return df
            except Exception:
                return df
    return df

def main():
    os.makedirs(os.path.dirname(GOLD_PATH), exist_ok=True)

    new_df = read_silver_df()
    new_df = ensure_revenue(new_df)

    nk = pick_natural_key(list(new_df.columns))
    if not nk:
        raise SystemExit(f"Cannot determine natural key from columns: {list(new_df.columns)}")
    print(f"[to_gold] Using natural key: {nk}")

    new_df["_nk"] = make_nk_series(new_df, nk)

    if os.path.exists(GOLD_PATH):
        old_df = pd.read_csv(GOLD_PATH)
        if "_nk" not in old_df.columns:
            missing = [c for c in nk if c not in old_df.columns]
            if missing:
                raise SystemExit(
                    f"Existing gold missing natural key columns {missing}; "
                    f"delete {GOLD_PATH} once or migrate columns."
                )
            old_df["_nk"] = make_nk_series(old_df, nk)
        combined = pd.concat([old_df, new_df], ignore_index=True).drop_duplicates("_nk", keep="last")
    else:
        combined = new_df.drop_duplicates("_nk", keep="last")

    if "_nk" in combined.columns:
        combined = combined.drop(columns=["_nk"])

    combined = sort_by_date_if_possible(combined)
    combined.to_csv(GOLD_PATH, index=False)
    print(f"[to_gold] Wrote {len(combined):,} rows to {GOLD_PATH}")

if __name__ == "__main__":
    main()
