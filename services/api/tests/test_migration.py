from pathlib import Path
from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.platform import Station, Sample, ImportRecord
from app.migration.monitoring import import_snapshot

ROOT=Path(__file__).resolve().parents[3]


def test_real_snapshot_is_exact_and_idempotent():
    with SessionLocal() as db:
        for cls in (Sample,Station,ImportRecord):
            db.query(cls).delete()
        db.commit()
        first=import_snapshot(db,ROOT/'data/public')
        again=import_snapshot(db,ROOT/'data/public')
        assert first==again
        assert first['stations']==1 and first['effluent_samples']==154
        assert db.get(Station,'PTG248').payload['name']=='PETALING-MAWAR'
        assert db.get(Sample,1).payload['no3n_bdl'] is True
        assert db.get(Sample,1).payload['no3n']==1.0
        assert db.query(Sample).count()==154


def test_changed_source_rejected(tmp_path):
    import shutil,pytest
    shutil.copytree(ROOT/'data/public',tmp_path/'snapshot')
    path=tmp_path/'snapshot/effluent_samples.csv'
    path.write_bytes(path.read_bytes()+b'\n')
    with SessionLocal() as db,pytest.raises(ValueError,match='changed'):
        import_snapshot(db,tmp_path/'snapshot')
