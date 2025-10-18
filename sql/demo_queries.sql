-- ① 看前 5 列
SELECT * FROM read_csv_auto('data/gold/fact_sales.csv') LIMIT 5;

-- ② 依地區(geo_id)彙總營收 Top 5
SELECT geo_id, SUM(revenue_jpy) AS rev_jpy
FROM read_csv_auto('data/gold/fact_sales.csv')
GROUP BY 1
ORDER BY rev_jpy DESC
LIMIT 5;

-- ③ 依日期彙總（order_date 是 YYYYMMDD 格式）
SELECT 
  strptime(CAST(order_date AS VARCHAR), '%Y%m%d') AS date,
  SUM(revenue_jpy) AS rev_jpy
FROM read_csv_auto('data/gold/fact_sales.csv')
GROUP BY 1
ORDER BY date
LIMIT 10;
