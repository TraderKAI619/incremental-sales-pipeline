# Quarantine Examples (Why rows are isolated)

## Bad Date Format
- Example: `20251535` (invalid day).
- Root cause: Upstream parsing bug.
- Action: Add ingestion-time date validation.

## Missing Geography
- Empty `geo_id` → cannot do regional rollups.
- Action: Make `geo_id` required or define fallback mapping.

## Negative Quantities
- Values like `-2` could be returns or entry errors.
- Decision: Route to `fact_returns` (separate fact), not revenue.

## Unknown Product
- `product_id=P999` not in dictionary.
- Action: Update dim or reject with reason; track rate over time.

See: `reports/dq_report.md`, `sql/create_returns_table.sql`.
