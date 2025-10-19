# scripts/validate_utils.py
from __future__ import annotations
import json, math
from pathlib import Path
import pandas as pd

def _coerce_dtype(sr: pd.Series, spec: dict):
    t = spec.get("dtype")
    if t == "string":
        return sr.astype("string")
    if t == "int":
        return pd.to_numeric(sr, errors="coerce").astype("Int64")
    if t == "float":
        return pd.to_numeric(sr, errors="coerce")
    if t == "date":
        fmt = spec.get("format", None)
        return pd.to_datetime(sr, errors="coerce", format=fmt).dt.date
    return sr  # fallback

def load_schema(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def validate_df(df: pd.DataFrame, schema: dict) -> dict:
    fields = schema["fields"]
    required = set(schema.get("required", []))
    pk = schema.get("primaryKey", [])
    report = {"errors": [], "warns": [], "counts": {}, "pk_duplicates": 0}

    # 欄位存在
    for col in required:
        if col not in df.columns:
            report["errors"].append(f"Missing required column: {col}")

    if report["errors"]:
        return report

    # 型別與基本約束
    for col, spec in fields.items():
        if col in df.columns:
            df[col] = _coerce_dtype(df[col], spec)
            # not-null 檢查
            if col in required:
                nulls = df[col].isna().sum()
                if nulls > 0:
                    report["errors"].append(f"NULLs in required column: {col} ({nulls})")
            # 範圍檢查（數值）
            if spec.get("dtype") in ("int", "float"):
                mn, mx = spec.get("min", None), spec.get("max", None)
                if mn is not None:
                    bad = (df[col] < mn).sum()
                    if bad:
                        report["errors"].append(f"{col} < {mn}: {bad} rows")
                if mx is not None:
                    bad = (df[col] > mx).sum()
                    if bad:
                        report["errors"].append(f"{col} > {mx}: {bad} rows")

    # PK 重複
    if pk:
        dup_count = df.duplicated(pk).sum()
        report["pk_duplicates"] = int(dup_count)
        if dup_count > 0:
            report["errors"].append(f"Primary key duplicates: {dup_count} rows")

    report["counts"]["rows"] = int(len(df))
    return report

def write_markdown(report_path: str | Path, title: str, items: dict):
    p = Path(report_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {title}", ""]
    for k, v in items.items():
        lines.append(f"- **{k}**: {v}")
    p.write_text("\n".join(lines), encoding="utf-8")
