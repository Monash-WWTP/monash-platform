"""Import an authorized owner-only JSON export; does not infer authorship from email."""

import argparse, json
from pathlib import Path
from app.db.session import SessionLocal
from app.migration.private import import_reports, import_private_bundle

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--export", type=Path, required=True)
p.add_argument("--source-id", required=True)
p.add_argument("--photo-root", type=Path)
a = p.parse_args()
if a.export.stat().st_mode & 0o077:
    raise ValueError("Private export must have owner-only permissions")
data = json.loads(a.export.read_text())
with SessionLocal() as db:
    if isinstance(data, dict):
        if not a.photo_root:
            raise ValueError("Photo bundle requires --photo-root")
        result = import_private_bundle(
            db, data["reports"], data["photos"], a.photo_root, a.source_id
        )
    else:
        result = import_reports(db, data, a.source_id)
    print(json.dumps(result))
