#!/usr/bin/env python3
"""Export the public WWTP monitoring dataset to ``public-data/``.

Pulls public, read-only monitoring tables from Supabase using the same
publishable key the frontend uses and writes a versioned snapshot. Derived
sample-level GHG views are excluded because the available samples are final
effluent, not the influent data required by their equations:

    public-data/
      stations.csv
      effluent_samples.csv
      emission_factors.csv
      *.parquet            (only if pandas + pyarrow are installed)
      manifest.json        (dataset version, generation time, row counts, commit)

CSV is always written with the stdlib (no third-party deps required). Parquet is
written too when ``pandas``/``pyarrow`` are importable. The script is
re-runnable and overwrites the snapshot in place.

Workflow for a citable release:
    1. python3 scripts/export_public_dataset.py
    2. commit public-data/
    3. tag a GitHub release  ->  Zenodo mints a DOI for that exact snapshot.

Usage:
    python3 scripts/export_public_dataset.py
Environment overrides (defaults are the public frontend values):
    SUPABASE_URL, SUPABASE_KEY
"""
from __future__ import annotations

import csv
import json
import os
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Bump on any schema/semantics change to the published columns (semver).
DATASET_VERSION = "1.1.0"

SUPABASE_URL = os.environ.get(
    "SUPABASE_URL", "https://eaxekwlmvpvftpgxiwlu.supabase.co"
).rstrip("/")
SUPABASE_KEY = os.environ.get(
    "SUPABASE_KEY", "sb_publishable_3-3Y9gvsPaJvErjgB80s6A__xFEcU1j"
)

OUT_DIR = Path(__file__).resolve().parent.parent / "public-data"

# Published tables/views, in dependency order. Each is fetched in full.
TABLES = [
    "stations",
    "effluent_samples",
    "emission_factors",
]
DEPRECATED_ARTIFACTS = ("ghg_sample_emissions", "ghg_station_year")

PAGE = 1000  # PostgREST per-request cap; we paginate to be safe.


def fetch_all(table: str) -> list[dict]:
    """Page through a table/view via PostgREST and return all rows."""
    rows: list[dict] = []
    start = 0
    while True:
        req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/{table}?select=*",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Range-Unit": "items",
                "Range": f"{start}-{start + PAGE - 1}",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            chunk = json.loads(resp.read())
        rows.extend(chunk)
        if len(chunk) < PAGE:
            return rows
        start += PAGE


def union_columns(rows: list[dict]) -> list[str]:
    """Stable column order: first row's keys, then any extras seen later."""
    cols: list[str] = []
    for row in rows:
        for key in row:
            if key not in cols:
                cols.append(key)
    return cols


def write_csv(path: Path, rows: list[dict], cols: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        writer.writerows(rows)


def git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=OUT_DIR.parent,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name in DEPRECATED_ARTIFACTS:
        for suffix in (".csv", ".parquet"):
            (OUT_DIR / f"{name}{suffix}").unlink(missing_ok=True)

    # Parquet needs pandas AND a parquet engine (pyarrow or fastparquet).
    have_parquet = False
    try:
        import pandas as pd  # noqa: F401
        import importlib.util

        have_parquet = any(
            importlib.util.find_spec(m) for m in ("pyarrow", "fastparquet")
        )
    except ImportError:
        pass
    if not have_parquet:
        print("note: pandas+pyarrow not available -> writing CSV only "
              "(pip install pandas pyarrow to also emit Parquet)")

    manifest_tables: dict[str, dict] = {}
    for table in TABLES:
        rows = fetch_all(table)
        cols = union_columns(rows) if rows else []
        write_csv(OUT_DIR / f"{table}.csv", rows, cols)
        if have_parquet and rows:
            import pandas as pd

            pd.DataFrame(rows, columns=cols).to_parquet(
                OUT_DIR / f"{table}.parquet", index=False
            )
        manifest_tables[table] = {"rows": len(rows), "columns": cols}
        print(f"exported {table:22} {len(rows):>5} rows")

    manifest = {
        "dataset": "Petaling WWTP effluent monitoring",
        "version": DATASET_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": SUPABASE_URL,
        "source_commit": git_commit(),
        "license": "CC-BY-4.0",
        "tables": manifest_tables,
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"\nwrote {OUT_DIR}/manifest.json (v{DATASET_VERSION})")


if __name__ == "__main__":
    main()
