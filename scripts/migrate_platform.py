"""Explicit monitoring import; database destination is supplied out of band."""
import argparse,json
from pathlib import Path
from app.db.session import SessionLocal
from app.migration.monitoring import import_snapshot

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--public-snapshot',type=Path,required=True)
p.add_argument('--reuse-identical',action='store_true',help='Reuse byte-equivalent existing row payloads; never overwrite changed records')
a=p.parse_args()
with SessionLocal() as db:
    print(json.dumps(import_snapshot(db,a.public_snapshot,reuse_identical=a.reuse_identical)))
