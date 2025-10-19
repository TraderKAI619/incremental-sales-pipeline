-- Track returns separately instead of quarantining
CREATE TABLE fact_returns AS
SELECT * FROM quarantine 
WHERE _bad_reason LIKE '%neg_or_zero_qty%';
EOF# Add a returns/adjustments table
cat > sql/create_returns_table.sql << 'EOF'
-- Track returns separately instead of quarantining
CREATE TABLE fact_returns AS
SELECT * FROM quarantine 
WHERE _bad_reason LIKE '%neg_or_zero_qty%';
