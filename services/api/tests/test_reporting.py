from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.identity.dependencies import require_account
from app.db.platform import Account
from app.db.session import SessionLocal


def account(capabilities):
    with SessionLocal() as db:
        item=Account(issuer='https://test-issuer.invalid',subject=str(uuid4()),email='test@example.com',capabilities=capabilities)
        db.add(item);db.commit();db.refresh(item);item._mfa_verified=True;return item


def test_owner_idempotency_and_privacy():
    citizen=account(['report:own']);other=account(['report:own']);reviewer=account(['report:review'])
    client=TestClient(app)
    app.dependency_overrides[require_account]=lambda:citizen
    body={'category':'wastewater','condition':'warning','latitude':3.065961,'longitude':101.628047,
          'note':'private note','observed_at':'2026-10-01T12:00:00Z'}
    try:
        headers={'Idempotency-Key':str(uuid4())}
        first=client.post('/api/v1/reports',json=body,headers=headers)
        assert first.status_code==201
        report=first.json()
        assert client.post('/api/v1/reports',json=body,headers=headers).json()['id']==report['id']
        assert client.post('/api/v1/reports',json={**body,'condition':'critical'},headers=headers).status_code==409
        app.dependency_overrides[require_account]=lambda:other
        assert client.get('/api/v1/reports/'+report['id']).status_code==404
        assert client.post('/api/v1/reports/'+report['id']+'/moderation',json={'status':'approved','reason':'reviewed'}).status_code==403
        app.dependency_overrides[require_account]=lambda:reviewer
        assert client.post('/api/v1/reports/'+report['id']+'/moderation',json={'status':'approved','reason':'reviewed'}).status_code==200
        public=client.get('/api/v1/community/observations').json()['items']
        row=next(r for r in public if r['id']==report['id'])
        assert not {'owner_id','note','photo_path','media_id','legacy_subject','location_accuracy_m'} & row.keys()
        assert row['latitude']==3.066 and row['longitude']==101.628
    finally:app.dependency_overrides.clear()


def test_category_units_are_validated():
    citizen=account(['report:own']);app.dependency_overrides[require_account]=lambda:citizen
    try:
        response=TestClient(app).post('/api/v1/reports',headers={'Idempotency-Key':str(uuid4())},json={
            'category':'rainfall','reading_value':-1,'reading_unit':'mm','latitude':0,'longitude':0,
            'observed_at':'2026-10-01T12:00:00Z'})
        assert response.status_code==422
    finally:app.dependency_overrides.clear()
