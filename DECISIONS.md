# Technical Decisions (ADR-lite)

1) Idempotent Incremental Upserts
- Natural key `[order_date, geo_id, product_id]` for deterministic merges.
- Trade-off: Composite index size vs. simplicity.

2) Quarantine over Hard Rejection
- Preserve lineage and enable RCA; unblock daily loads.
- Trade-off: Storage overhead; needs cleanup & metrics.

3) CSV Artifacts for Portfolio
- Readable, previewable; CI attaches gold/report.
- Trade-off: Performance; prod → Parquet + partitioning.

4) DuckDB for Local Batch
- Zero infra, fast iteration; good for CI.
- Path: S3 + Glue/Athena for cloud scale.

5) Minimal Yet Meaningful DQ Set
- Start with schema + business rules; expand via tests/dashboard.
- Path: Great Expectations or dbt tests later.
