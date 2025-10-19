from pathlib import Path
import subprocess, hashlib

def md5(p): return hashlib.md5(Path(p).read_bytes()).hexdigest()

def test_idempotent_twice():
    subprocess.check_call(["make","run"])
    h1 = md5("data/gold/fact_sales.csv")
    subprocess.check_call(["make","run"])
    h2 = md5("data/gold/fact_sales.csv")
    assert h1 == h2
