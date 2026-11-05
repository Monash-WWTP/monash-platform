import json
import shutil
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.models import Base
from app.db.platform import Sample, Station
from app.migration.monitoring import import_snapshot

SOURCE = Path(__file__).resolve().parents[1] / 'data/public'

def test_refresh_reuses_identical_records_and_rejects_changed_history(tmp_path):
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    shutil.copytree(SOURCE, tmp_path / 'refresh')
    manifest = tmp_path / 'refresh/manifest.json'
    metadata = json.loads(manifest.read_text())
    metadata['version'] = 'refresh-test'
    manifest.write_text(json.dumps(metadata))
    with Session(engine) as db:
        original = import_snapshot(db, SOURCE)
        assert import_snapshot(db, tmp_path / 'refresh', reuse_identical=True) == original
        assert db.query(Station).count() == 1
        assert db.query(Sample).count() == 154
        assert import_snapshot(db, tmp_path / 'refresh', reuse_identical=True) == original
        metadata['version'] = 'changed-test'
        manifest.write_text(json.dumps(metadata))
        station = tmp_path / 'refresh/stations.csv'
        station.write_text(station.read_text().replace('PETALING-MAWAR', 'Changed name'))
        with pytest.raises(ValueError, match='differs'):
            import_snapshot(db, tmp_path / 'refresh', reuse_identical=True)
        db.rollback()
        assert db.get(Station, 'PTG248').payload['name'] == 'PETALING-MAWAR'
