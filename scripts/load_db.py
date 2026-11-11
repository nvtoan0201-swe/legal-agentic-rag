"""Load data/processed/*.parquet into PostgreSQL (drops and recreates the tables).

make up && uv run python -I scripts/load_db.py
"""

import argparse
from pathlib import Path

from legalrag.config import settings
from legalrag.db import load

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dsn", default=settings.postgres_dsn)
    ap.add_argument("--processed", type=Path, default=Path("data/processed"))
    args = ap.parse_args()
    print(load(args.dsn, args.processed))
