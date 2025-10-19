from __future__ import annotations
import json
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
        return pd.to_datetime(sr, errors="coerce", format=spec.get("format")).dt.date
    return sr

def load_schema(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def validate_df(df: pd.DataFrame, schema: dict) -> dict:
    fields = schema["fields"]
    required = set(schema.get("required", []))
    pk = schema.get("primaryKey", [])
    rep = {"errors": [], "counts": {}, "pk_duplicates": 0}

    # 欄位存在
    for col in required:
        if col not in df.columns:
            rep["errors"].append(f"Missing required column: {col}")

    if rep["errors"]:
        return rep

    # 型別 + NULL + 範圍
    for col, spec in fields.items():
        if col in df.columns:
            df[col] = _coerce_dtype(df[col], spec)
            if col in required:
                nnull = int(df[col].isna().sum())
                if nnull:
                    rep["errors"].append(f"NULLs in required column {col}: {nnull}")
            if spec.get("dtype") in ("int", "float"):
                mn, mx = spec.get("min"), spec.get("max")
                if mn is not None:
                    bad = int((df[col] < mn).sum())
                    if bad:
                        rep["errors"].append(f"{col} < {mn}: {bad} rows")
                if mx is not None:
                    bad = int((df[col] > mx).sum())
                    if bad:
                        rep["errors"].append(f"{col} > {mx}: {bad} rows")

    # PK 重複
    if pk:
        dup = int(df.duplicated(pk).sum())
        rep["pk_duplicates"] = dup
        if dup:
            rep["errors"].append(f"Primary key duplicates: {dup} rows")

    rep["counts"]["rows"] = int(len(df))
    return rep

def write_markdown(report_path: str | Path, title: str, items: dict):
    p = Path(report_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {title}", ""]
    for k, v in items.items():
        lines.append(f"- **{k}**: {v}")
    p.write_text("\n".join(lines), encoding="utf-8")
