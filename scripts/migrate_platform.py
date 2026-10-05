"""Explicit monitoring import; database destination is supplied out of band."""
import argparse,json
from pathlib import Path
from app.db.session import SessionLocal
from app.migration.monitoring import import_snapshot

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--public-snapshot',type=Path,required=True)
a=p.parse_args()
with SessionLocal() as db:
    print(json.dumps(import_snapshot(db,a.public_snapshot)))
