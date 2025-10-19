#!/usr/bin/env python3
"""Update quarantine trend tracking"""
import pandas as pd
import glob
from datetime import datetime
from pathlib import Path

def update_trends():
    trends_file = Path('reports/quarantine_trends.csv')
    
    # Load current data
    gold = pd.read_csv('data/gold/fact_sales.csv')
    quar_files = glob.glob('data/silver/quarantine/*.csv')
    quarantine = pd.concat([pd.read_csv(f) for f in quar_files]) if quar_files else pd.DataFrame()
    
    total = len(gold) + len(quarantine)
    good = len(gold)
    bad = len(quarantine)
    rate = (bad / total * 100) if total > 0 else 0
    
    # Create or append to trends file
    new_row = {
        'Date': datetime.now().strftime('%Y-%m-%d'),
        'Total': total,
        'Good': good,
        'Bad': bad,
        'Rate': f"{rate:.1f}%"
    }
    
    if trends_file.exists():
        df = pd.read_csv(trends_file)
        # Check if today already exists
        today = new_row['Date']
        if today not in df['Date'].values:
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    else:
        df = pd.DataFrame([new_row])
    
    df.to_csv(trends_file, index=False)
    print(f"✅ Updated quarantine trends: {bad}/{total} ({rate:.1f}%)")

if __name__ == '__main__':
    update_trends()
