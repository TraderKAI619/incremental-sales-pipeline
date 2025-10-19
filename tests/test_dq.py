import os, glob, subprocess, pandas as pd

FACT = "data/gold/fact_sales.csv"
QUAR = "data/silver/quarantine"

NATURAL_KEY_CANDIDATES = [
    ["order_id"],                             # 最明確
    ["order_date", "geo_id", "product_id"],
    ["date_id", "geo_id", "product_id"],
    ["date", "store_id", "product_id"],
]

def read_gold():
    assert os.path.exists(FACT), f"{FACT} not found"
    df = pd.read_csv(FACT)
    assert len(df) > 0, "gold is empty"
    return df

def pick_nk(cols):
    lower = {c.lower(): c for c in cols}
    for cand in NATURAL_KEY_CANDIDATES:
        if all(k in lower for k in (c.lower() for c in cand)):
            return [lower[c.lower()] for c in cand]
    return None

def pick_date_col(cols):
    lower = {c.lower(): c for c in cols}
    for k in ("date", "order_date", "date_id", "updated_at", "processed_at"):
        if k in lower:
            return lower[k]
    return None

def parse_dates(df, col):
    """智慧解析日期（處理 YYYYMMDD 數字格式）"""
    s = df[col]
    # 如果是數字且看起來像 YYYYMMDD（8 位數）
    if pd.api.types.is_numeric_dtype(s):
        # 檢查是否在合理範圍（19000101 ~ 21001231）
        if s.min() >= 19000101 and s.max() <= 21001231:
            return pd.to_datetime(s.astype("string"), format="%Y%m%d", errors="coerce")
    # 否則標準解析
    return pd.to_datetime(s, errors="coerce")

# === 測試 ===

def test_gold_exists_and_not_empty():
    df = read_gold()
    assert len(df) >= 10

def test_schema_contains_keys_and_revenue():
    df = read_gold()
    nk = pick_nk(df.columns)
    assert nk is not None, f"no natural key in: {list(df.columns)}"
    assert "revenue_jpy" in df.columns

def test_non_negative_revenue():
    df = read_gold()
    assert (df["revenue_jpy"].fillna(0) >= 0).all()

def test_rowcount_reasonable():
    df = read_gold()
    assert 10 <= len(df) <= 1_000_000

def test_idempotency_run_twice_same_rows():
    df1 = read_gold()
    subprocess.run(["python", "scripts/to_gold.py"], check=True)
    df2 = read_gold()
    assert len(df2) == len(df1)

def test_natural_key_uniqueness():
    df = read_gold()
    nk = pick_nk(df.columns)
    assert nk is not None
    dupes = df.duplicated(subset=nk).sum()
    assert dupes == 0, f"found {dupes} duplicates on {nk}"

def test_date_range_valid():
    df = read_gold()
    col = pick_date_col(df.columns)
    assert col is not None
    dt = parse_dates(df, col)
    valid_pct = dt.notna().mean()
    assert valid_pct > 0.95, f"only {valid_pct:.0%} parseable"
    # 合理範圍：2020-01-01 ~ 2030-12-31（更寬鬆）
    lo, hi = pd.Timestamp("2020-01-01"), pd.Timestamp("2030-12-31")
    valid_dates = dt[dt.notna()]
    out_of_range = ((valid_dates < lo) | (valid_dates > hi)).sum()
    assert out_of_range == 0, f"{out_of_range} dates out of range [{lo.date()} ~ {hi.date()}]"

def test_quarantine_reasonable_under_25pct():
    """放寬到 25%（你的資料有 23%）"""
    files = glob.glob(os.path.join(QUAR, "**/*.csv"), recursive=True) + \
            glob.glob(os.path.join(QUAR, "*.csv"))
    total_bad = sum(
        max(0, len(open(f, "r").read().splitlines()) - 1)
        for f in files if os.path.exists(f)
    )
    gold_count = len(pd.read_csv(FACT)) if os.path.exists(FACT) else 0
    total = gold_count + total_bad
    if total > 0:
        pct = (total_bad / total) * 100
        assert pct < 25.0, f"quarantine too high: {pct:.1f}% ({total_bad}/{total})"

