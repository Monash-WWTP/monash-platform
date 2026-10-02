"""Upload data-to-upload/ CSVs + station locations to Supabase.

Runs DDL-free inserts through the Supabase Management API using the CLI's
access token (macOS keychain). Idempotent: upserts station, skips duplicate
samples via the (station_code, sample_date, sampling) unique constraint.

Usage:  python3 scripts/upload_to_supabase.py
"""
from __future__ import annotations

import csv
import json
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path

PROJECT_REF = "eaxekwlmvpvftpgxiwlu"
API = f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query"
DATA_DIR = Path(__file__).resolve().parent.parent / "data-to-upload"

# CSV column -> (db column, is numeric metric with possible "< x" notation)
METRICS = {
    "BOD": "bod",
    "COD": "cod",
    "NH3N": "nh3n",
    "NO3N": "no3n",
    "pH": "ph",
    "O&G": "oil_grease",
    "TSS": "tss",
}


def get_token() -> str:
    return subprocess.check_output(
        ["security", "find-generic-password", "-l", "Supabase CLI", "-w"], text=True
    ).strip()


def run_sql(token: str, query: str):
    req = urllib.request.Request(
        API,
        data=json.dumps({"query": query}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "curl/8.7.1",  # Cloudflare blocks Python-urllib UA
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def parse_metric(raw: str) -> tuple[float | None, bool]:
    """'< 1.0' -> (1.0, True);  '7.4' -> (7.4, False);  '' -> (None, False)."""
    raw = (raw or "").strip()
    if not raw:
        return None, False
    if raw.startswith("<"):
        return float(raw.lstrip("<").strip()), True
    try:
        return float(raw), False
    except ValueError:
        return None, False


def sql_val(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def main() -> None:
    token = get_token()
    locations = json.loads((DATA_DIR / "station_locations.json").read_text())

    rows = []
    station_meta: dict[str, dict] = {}
    for csv_path in sorted(DATA_DIR.glob("*.csv")):
        year = int(csv_path.stem)
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            for rec in csv.DictReader(f):
                code = rec["Code"].strip()
                station_meta[code] = {
                    "name": rec["NAME"].strip(),
                    "stp_type": rec.get("STP_Type", "").strip(),
                    "category": (rec.get("STP_CATEGORY") or rec.get("DESIGN") or "B").strip(),
                }
                date = datetime.strptime(rec["Date"].strip(), "%d-%b-%y").date()
                row = {
                    "station_code": code,
                    "sample_date": date.isoformat(),
                    "sampling": int(rec.get("Sampling") or 0),
                    "sample_point": rec.get("Sample_Point", "").strip(),
                    "temperature": parse_metric(rec.get("TEMP", ""))[0],
                    "compliance": (rec.get("EQA2009") or rec.get("COMPLIANCE_TO") or "").strip(),
                    "source_year": year,
                }
                for col, db_col in METRICS.items():
                    val, bdl = parse_metric(rec.get(col, ""))
                    row[db_col] = val
                    row[f"{db_col}_bdl"] = bdl
                rows.append(row)

    # upsert stations
    for code, meta in station_meta.items():
        loc = locations.get(code)
        if not loc:
            print(f"WARNING: no location for {code}, skipping station")
            continue
        run_sql(
            token,
            f"""insert into public.stations (code, name, stp_type, category, latitude, longitude)
            values ({sql_val(code)}, {sql_val(meta['name'])}, {sql_val(meta['stp_type'])},
                    {sql_val(meta['category'])}, {loc['latitude']}, {loc['longitude']})
            on conflict (code) do update set
              name = excluded.name, stp_type = excluded.stp_type,
              category = excluded.category,
              latitude = excluded.latitude, longitude = excluded.longitude;""",
        )
        print(f"station upserted: {code} ({meta['name']})")

    # batch insert samples
    cols = list(rows[0].keys())
    BATCH = 50
    inserted = 0
    for i in range(0, len(rows), BATCH):
        batch = rows[i : i + BATCH]
        values = ",\n".join(
            "(" + ", ".join(sql_val(r[c]) for c in cols) + ")" for r in batch
        )
        run_sql(
            token,
            f"""insert into public.effluent_samples ({', '.join(cols)})
            values {values}
            on conflict (station_code, sample_date, sampling) do nothing;""",
        )
        inserted += len(batch)
        print(f"samples processed: {inserted}/{len(rows)}")

    count = run_sql(token, "select count(*) as n from public.effluent_samples;")
    print(f"total samples in supabase: {count[0]['n']}")


if __name__ == "__main__":
    main()
