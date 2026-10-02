import csv
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_inactive_references_and_public_data_preserve_original_bytes():
    inventory = json.loads((ROOT / "docs/migration/source-inventory.json").read_text())
    adaptations = {"data/public/DATA_DICTIONARY.md"}
    for row in inventory["files"]:
        target = row.get("target_path", "")
        if target and (row["disposition"] == "legacy_reference" or target.startswith("data/public/")) and target not in adaptations:
            assert hashlib.sha256((ROOT / target).read_bytes()).hexdigest() == row["source_sha256"], target


def test_public_snapshot_matches_published_manifest():
    manifest = json.loads((ROOT / "data/public/manifest.json").read_text())
    assert manifest["license"] == "CC-BY-4.0"
    for table, info in manifest["tables"].items():
        with (ROOT / f"data/public/{table}.csv").open() as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == info["columns"]
            assert len(list(reader)) == info["rows"]


def test_notebook_uses_pinned_local_snapshot():
    notebook = json.loads((ROOT / "research/notebooks/wwtp_explore.ipynb").read_text())
    code = "\n".join("".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code")
    assert "urlopen" not in code and "https://" not in code
    assert 'data/public' in code
