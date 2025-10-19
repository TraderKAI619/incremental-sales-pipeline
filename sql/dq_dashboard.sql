-- Data Quality Dashboard
-- Run with: duckdb < sql/dq_dashboard.sql || python3 scripts/run_sql.py sql/dq_dashboard.sql

.print === DATA QUALITY DASHBOARD ===
.print

-- 1. Overall metrics
.print --- Overall Metrics ---
SELECT 
    COUNT(*) as total_gold_records,
    (SELECT COUNT(*) FROM read_csv('data/silver/quarantine/*.csv')) as quarantined_records,
    ROUND(COUNT(*) * 100.0 / (COUNT(*) + (SELECT COUNT(*) FROM read_csv('data/silver/quarantine/*.csv'))), 2) as pass_rate_pct
FROM 'data/gold/fact_sales.csv';

.print
.print --- Top Revenue Products ---
SELECT 
    product_id,
    SUM(revenue_jpy) as total_revenue,
    COUNT(*) as order_count,
    ROUND(AVG(revenue_jpy), 2) as avg_revenue
FROM 'data/gold/fact_sales.csv'
GROUP BY product_id
ORDER BY total_revenue DESC
LIMIT 5;

.print
.print --- Geographic Performance ---
SELECT 
    geo_id,
    COUNT(DISTINCT order_date) as active_days,
    COUNT(*) as total_orders,
    SUM(revenue_jpy) as total_revenue
FROM 'data/gold/fact_sales.csv'
GROUP BY geo_id
ORDER BY total_revenue DESC;

.print
.print --- Quality Issues by Product ---
SELECT 
    product_id,
    COUNT(*) as issue_count,
    STRING_AGG(DISTINCT _bad_reason, ', ') as issue_types
FROM read_csv('data/silver/quarantine/*.csv')
GROUP BY product_id
ORDER BY issue_count DESC;
