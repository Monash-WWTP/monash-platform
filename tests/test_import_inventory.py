import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/migration/source-inventory.json"
CHECKER = ROOT / "scripts/check_import_inventory.py"
ALLOWED = {"imported", "superseded", "legacy_reference", "generated", "restricted", "omitted"}


def test_every_pinned_source_file_has_one_disposition():
    assert MANIFEST.exists(), "source inventory must exist"
    rows = json.loads(MANIFEST.read_text())["files"]
    assert len(rows) == 207
    keys = [(row["source_repo"], row["source_path"]) for row in rows]
    assert len(keys) == len(set(keys))
    for row in rows:
        assert row["disposition"] in ALLOWED
        assert len(row["source_sha256"]) == 64
        assert row.get("target_path") or row.get("reason")


def test_inventory_matches_pinned_git_trees():
    result = subprocess.run(
        [sys.executable, str(CHECKER),
         "--source", "citizenflood=/home/jienweng/projects/citizenflood",
         "--source", "dashboard=/home/jienweng/projects/wwtp-dashboard",
         "--source", "api=/home/jienweng/projects/monash-platform-api"],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
