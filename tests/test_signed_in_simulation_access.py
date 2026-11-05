from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.main import app
from app.db.models import Base, Plant
from app.db.platform import Account
from app.db.session import get_db
from app.identity.dependencies import require_account


def test_signed_in_citizen_can_use_lab_but_not_administration():
    engine = create_engine('sqlite://', poolclass=StaticPool,
                           connect_args={'check_same_thread': False})
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(Plant(id=1, code='TEST', name='Synthetic test', latitude=0,
                     longitude=0, capacity_mld=10))
        db.commit()
    def database():
        with Session(engine) as db:
            yield db
    saved = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = database
    try:
        with TestClient(app) as client:
            assert client.get('/api/v1/plants/1/scenarios').status_code == 401
            account = Account(id='citizen', capabilities=['report:own'])
            app.dependency_overrides[require_account] = lambda: account
            assert client.get('/api/v1/plants/1/scenarios').status_code == 200
            created = client.post('/api/v1/plants/1/scenarios', json={'name': 'Citizen research', 'horizon': '1_month'})
            assert created.status_code == 201, created.text
            scenario = created.json()['id']
            run = client.post(f'/api/v1/scenarios/{scenario}/run', json={'start_date': '2026-11-05'})
            assert run.status_code == 201, run.text
            assert run.json()['status'] == 'completed'
            assert client.get('/api/v1/admin/users').status_code == 403
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(saved)
        engine.dispose()
