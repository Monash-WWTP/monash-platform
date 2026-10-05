from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.db.platform import Account,CitizenReport
from app.identity.dependencies import require_account
from app.migration.private import import_reports
from app.routers import migration_claim


def test_claim_requires_original_subject_not_matching_email(monkeypatch):
    subject=str(uuid4());identifier=str(uuid4())
    with SessionLocal() as db:
        native=Account(issuer='https://native.test/',subject=str(uuid4()),email='same-email@example.test')
        db.add(native);db.commit();db.refresh(native)
        import_reports(db,[{'id':identifier,'reporter_id':subject,'category':'wastewater','condition':'normal','latitude':0,'longitude':0,
            'observed_at':'2025-01-01T00:00:00Z','created_at':'2025-01-02T00:00:00Z','moderation_status':'pending'}],'claim-'+identifier)
    app.dependency_overrides[require_account]=lambda:native
    client=TestClient(app)
    try:
        monkeypatch.setattr(migration_claim,'legacy_subject',lambda token:str(uuid4()))
        assert client.post('/api/v1/migration/claim-reports',json={'legacy_access_token':'isolated-proof'}).json()['claimed']==0
        with SessionLocal() as db:assert db.get(CitizenReport,identifier).owner_id is None
        monkeypatch.setattr(migration_claim,'legacy_subject',lambda token:subject)
        assert client.post('/api/v1/migration/claim-reports',json={'legacy_access_token':'isolated-proof'}).json()['claimed']==1
        with SessionLocal() as db:assert db.get(CitizenReport,identifier).owner_id==native.id
        assert client.post('/api/v1/migration/claim-reports',json={'legacy_access_token':'isolated-proof'}).json()['claimed']==0
    finally:app.dependency_overrides.clear()
