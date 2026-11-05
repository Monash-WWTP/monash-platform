"""Read allowlisted public monitoring tables into a versioned local snapshot.

No source writes. Supply SUPABASE_URL and SUPABASE_KEY out of band. Existing
snapshots are never overwritten. Import separately after inspecting counts.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]

def snapshot(destination: Path, source: str, key: str) -> dict:
    if urlsplit(source).scheme != 'https' or urlsplit(source).path not in ('', '/'):
        raise ValueError('An HTTPS source origin is required')
    template = json.loads((ROOT / 'data/public/manifest.json').read_text())
    collected = {}
    for table, spec in template['tables'].items():
        records = []
        for offset in range(0, 100000, 500):
            query = urlencode({'select': ','.join(spec['columns']), 'offset': offset,
                               'limit': 500, 'order': 'code' if table == 'stations' else 'id' if table == 'effluent_samples' else 'process_type'})
            request = Request(f'{source.rstrip("/")}/rest/v1/{table}?{query}', headers={'apikey': key})
            with urlopen(request, timeout=30) as response:
                page = json.load(response)
            if not isinstance(page, list):
                raise ValueError('Invalid monitoring response')
            records.extend({column: row[column] for column in spec['columns']} for row in page)
            if len(page) < 500:
                break
        else:
            raise ValueError('Snapshot exceeds the bounded export size')
        collected[table] = records
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    os.chmod(destination, 0o700)
    manifest = {**template, 'version': datetime.now(timezone.utc).isoformat(),
                'generated_at': datetime.now(timezone.utc).isoformat(), 'source': source,
                'source_commit': None, 'capture': 'read-only public REST snapshot',
                'license': 'See original source rights; new rows require review before redistribution',
                'tables': {}, 'sha256': {}}
    for table, records in collected.items():
        columns = template['tables'][table]['columns']
        path = destination / f'{table}.csv'
        with path.open('x', newline='') as stream:
            os.chmod(path, 0o600)
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            writer.writerows(records)
        manifest['tables'][table] = {'rows': len(records), 'columns': columns}
        manifest['sha256'][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    path = destination / 'manifest.json'
    path.write_text(json.dumps(manifest, indent=2) + '\n')
    os.chmod(path, 0o600)
    return {table: len(records) for table, records in collected.items()}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(snapshot(args.destination, os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])))
