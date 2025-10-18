import os, glob, subprocess, pandas as pd
FACT = "data/gold/fact_sales.csv"
QUAR = "data/silver/quarantine"

NK_CANDIDATES = [
    ["date", "store_id", "product_id"],
    ["order_date", "store_id", "product_id"],
    ["date", "store_id", "sku"],
    ["ts", "store_id", "product_id"],
    ["yyyymmdd", "store_id", "product_id"],
]

def read_gold():
    assert os.path.exists(FACT), f"{FACT} not found (run `make gold` first)"
    df = pd.read_csv(FACT)
    assert len(df) > 0, "gold is empty"
    return df

def pick_nk(cols):
    lower = {c.lower(): c for c in cols}
    for cand in NK_CANDIDATES:
        if all(k in lower for k in (c.lower() for c in cand)):
            return [lower[c.lower()] for c in cand]
    return None

def pick_date_col(cols):
    lower = {c.lower(): c for c in cols}
    for k in ("date","order_date","ts","yyyymmdd"):
        if k in lower: return lower[k]
    return None

def test_gold_exists_and_not_empty():
    df = read_gold()
    assert len(df) >= 10

def test_schema_contains_keys_and_revenue():
    df = read_gold()
    nk = pick_nk(df.columns)
    assert nk is not None, f"no natural key found in columns: {list(df.columns)}"
    assert "revenue_jpy" in df.columns, "revenue_jpy missing (to_gold should fail fast otherwise)"

def test_non_negative_revenue():
    df = read_gold()
    assert (df["revenue_jpy"].fillna(0) >= 0).all(), "found negative revenue"

def test_rowcount_reasonable():
    df = read_gold()
    assert 10 <= len(df) <= 1_000_000, f"rowcount out of range: {len(df)}"

def test_idempotency_run_twice_same_rows():
    df1 = read_gold()
    # 再跑一次 gold（冪等不應增加列數）
    subprocess.run(["python", "scripts/to_gold.py"], check=True)
    df2 = read_gold()
    assert len(df2) == len(df1), f"idempotency violated: {len(df1)} -> {len(df2)}"

def test_natural_key_uniqueness():
    df = read_gold()
    nk = pick_nk(df.columns)
    assert nk is not None
    dupes = df.duplicated(subset=nk).sum()
    assert dupes == 0, f"found {dupes} duplicate natural keys on {nk}"

def test_date_range_valid():
    df = read_gold()
    col = pick_date_col(df.columns)
    assert col is not None, "no date/ts/yyyymmdd column"
    s = df[col]
    try:
        if col.lower() == "yyyymmdd":
            dt = pd.to_datetime(s.astype("string"), format="%Y%m%d", errors="coerce")
        elif col.lower() == "ts" and pd.api.types.is_numeric_dtype(s):
            unit = "ms" if pd.to_numeric(s, errors="coerce").max() > 1e12 else "s"
            dt = pd.to_datetime(s, unit=unit, errors="coerce")
        else:
            dt = pd.to_datetime(s, errors="coerce")
    except Exception as e:
        raise AssertionError(f"cannot parse date column {col}: {e}")
    assert dt.notna().mean() > 0.95, "too many unparseable dates"
    assert dt.min() >= pd.Timestamp("2000-01-01"), f"min date too small: {dt.min()}"
    assert dt.max() <= pd.Timestamp("2100-12-31"), f"max date too large: {dt.max()}"

def test_quarantine_reasonable_under_5pct():
    # 允許少量壞資料，但不該超過 5%
    files = glob.glob(os.path.join(QUAR, "**/*.csv"), recursive=True) + \
            glob.glob(os.path.join(QUAR, "*.csv"))
    total_bad = 0
    for fpath in files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                rows = f.read().splitlines()
            total_bad += max(0, len(rows) - 1)  # 扣掉 header
        except FileNotFoundError:
            pass
    gold = pd.read_csv(FACT) if os.path.exists(FACT) else pd.DataFrame()
    gold_count = len(gold)
    total_expected = gold_count + total_bad
    if total_expected > 0:
        bad_pct = (total_bad / total_expected) * 100
        assert bad_pct < 5.0, f"quarantine too high: {bad_pct:.1f}% ({total_bad}/{total_expected})"
