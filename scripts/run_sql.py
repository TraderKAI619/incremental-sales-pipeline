#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, duckdb, pathlib
def main():
    if len(sys.argv)<2:
        print("Usage: python scripts/run_sql.py sql/demo_queries.sql"); return
    p=pathlib.Path(sys.argv[1]); con=duckdb.connect()
    with open(p,"r",encoding="utf-8") as f: sql=f.read()
    for i,s in enumerate([x.strip() for x in sql.split(";") if x.strip()],1):
        print(f"\n-- Statement {i} --")
        try: print(con.execute(s).df().head(50).to_string(index=False))
        except Exception as e: print(f"[ERROR] {e}")
    con.close()
if __name__=="__main__": main()
