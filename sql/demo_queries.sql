-- 看前 5 列
SELECT * FROM read_csv_auto('data/gold/fact_sales.csv') LIMIT 5;

-- 依商店彙總營收 Top 5
SELECT store_id, SUM(revenue_jpy) AS rev_jpy
FROM read_csv_auto('data/gold/fact_sales.csv')
GROUP BY 1
ORDER BY rev_jpy DESC
LIMIT 5;

-- 依日期彙總（若有 date 欄位）
SELECT date, SUM(revenue_jpy) AS rev_jpy
FROM read_csv_auto('data/gold/fact_sales.csv')
GROUP BY 1
ORDER BY date
LIMIT 10;
