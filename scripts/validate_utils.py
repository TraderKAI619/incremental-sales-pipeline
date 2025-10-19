#!/usr/bin/env python3
"""Validation utilities for schema-based data quality checks"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from typing import Dict, Any

def _coerce_dtype(sr: pd.Series, spec: dict):
    """Convert series to expected dtype"""
    t = spec.get("dtype")
    if t == "string":
        return sr.astype("string")
    if t == "int":
        return pd.to_numeric(sr, errors="coerce").astype("Int64")
    if t == "float":
        return pd.to_numeric(sr, errors="coerce")
    if t == "date":
        fmt = spec.get("format", "%Y%m%d")
        return pd.to_datetime(sr, errors="coerce", format=fmt).dt.date
    return sr

def load_schema(path: str | Path) -> dict:
    """Load JSON schema from file"""
    return json.loads(Path(path).read_text(encoding="utf-8"))

def validate_df(df: pd.DataFrame, schema: dict) -> dict:
    """
    Validate DataFrame against schema.
    
    Schema format:
    {
        "fields": [
            {"name": "col1", "dtype": "string"},
            {"name": "col2", "dtype": "int"},
            ...
        ],
        "required": ["col1", "col2"],
        "primaryKey": ["col1"]
    }
    """
    fields = schema.get("fields", [])
    required = set(schema.get("required", []))
    pk = schema.get("primaryKey", [])
    
    report = {
        "errors": [],
        "counts": {
            "rows": len(df)
        },
        "pk_duplicates": 0
    }
    
    # Check required columns exist
    for col in required:
        if col not in df.columns:
            report["errors"].append(f"Missing required column: {col}")
    
    if report["errors"]:
        return report
    
    # Validate each field
    for field_spec in fields:
        col_name = field_spec.get("name")
        if col_name not in df.columns:
            continue
            
        # Check nulls
        if col_name in required:
            null_count = df[col_name].isna().sum()
            if null_count > 0:
                report["counts"][f"{col_name}_nulls"] = int(null_count)
        
        # Type coercion (optional, for future use)
        # df[col_name] = _coerce_dtype(df[col_name], field_spec)
    
    # Check primary key duplicates
    if pk:
        pk_cols = [c for c in pk if c in df.columns]
        if pk_cols:
            duplicates = df.duplicated(subset=pk_cols, keep=False).sum()
            report["pk_duplicates"] = int(duplicates)
            if duplicates > 0:
                report["errors"].append(f"Primary key duplicates: {duplicates}")
    
    return report

def write_markdown(path: str | Path, title: str, data: Dict[str, Any]) -> None:
    """Write validation report as markdown"""
    lines = [f"# {title}\n"]
    for key, val in data.items():
        lines.append(f"- **{key}**: {val}")
    
    Path(path).write_text("\n".join(lines), encoding="utf-8")
