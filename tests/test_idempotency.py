# tests/test_idempotency.py
from pathlib import Path
import subprocess, hashlib

def filehash(p): 
    return hashlib.md5(Path(p).read_bytes()).hexdigest()

def test_idempotent_twice(tmp_path):
    subprocess.check_call(["make", "run"])
    h1 = filehash("data/gold/fact_sales.csv")
    subprocess.check_call(["make", "run"])
    h2 = filehash("data/gold/fact_sales.csv")
    assert h1 == h2, "Gold output changed on re-run -> not idempotent"
