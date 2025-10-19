#!/usr/bin/env python3
"""Data Quality Dashboard - Comprehensive metrics"""
import pandas as pd
import glob
from pathlib import Path

def main():
    # Load data
    gold = pd.read_csv('data/gold/fact_sales.csv')
    quar_files = glob.glob('data/silver/quarantine/*.csv')
    quarantine = pd.concat([pd.read_csv(f) for f in quar_files]) if quar_files else pd.DataFrame()
    
    print("=" * 60)
    print("           DATA QUALITY DASHBOARD")
    print("=" * 60)
    
    # 1. Overall Metrics
    print("\n--- Overall Metrics ---")
    total_records = len(gold) + len(quarantine)
    pass_rate = (len(gold) / total_records * 100) if total_records > 0 else 0
    print(f"Total Gold Records:     {len(gold):,}")
    print(f"Quarantined Records:    {len(quarantine):,}")
    print(f"Pass Rate:              {pass_rate:.2f}%")
    
    # 2. Top Revenue Products
    print("\n--- Top Revenue Products ---")
    top_products = gold.groupby('product_id').agg({
        'revenue_jpy': ['sum', 'count', 'mean']
    }).round(2)
    top_products.columns = ['Total Revenue', 'Order Count', 'Avg Revenue']
    top_products = top_products.sort_values('Total Revenue', ascending=False).head(5)
    print(top_products.to_string())
    
    # 3. Geographic Performance
    print("\n--- Geographic Performance ---")
    geo_perf = gold.groupby('geo_id').agg({
        'order_date': 'nunique',
        'order_id': 'count',
        'revenue_jpy': 'sum'
    }).round(2)
    geo_perf.columns = ['Active Days', 'Total Orders', 'Total Revenue']
    geo_perf = geo_perf.sort_values('Total Revenue', ascending=False)
    print(geo_perf.to_string())
    
    # 4. Quality Issues by Product
    if not quarantine.empty:
        print("\n--- Quality Issues by Product ---")
        issues = quarantine.groupby('product_id').agg({
            '_bad_reason': ['count', lambda x: ', '.join(x.unique())]
        })
        issues.columns = ['Issue Count', 'Issue Types']
        issues = issues.sort_values('Issue Count', ascending=False)
        print(issues.to_string())
    
    # 5. Returns Analysis
    returns_file = Path('data/gold/fact_returns.csv')
    if returns_file.exists():
        returns = pd.read_csv(returns_file)
        print(f"\n--- Returns/Adjustments ---")
        print(f"Total Returns:          {len(returns):,}")
        if not returns.empty:
            print(f"Most Returned Products: {returns['product_id'].value_counts().head(3).to_dict()}")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
