from fastapi.testclient import TestClient
from app.main import app


def test_database_readiness():
    result = TestClient(app).get('/api/v1/ready')
    assert result.status_code == 200
    assert result.json() == {'status': 'ready'}


def test_database_outage_is_not_ready(monkeypatch):
    from app.routers import readiness
    def unavailable():
        raise OSError('private connection details')
    monkeypatch.setattr(readiness, 'check_database', unavailable)
    result = TestClient(app).get('/api/v1/ready')
    assert result.status_code == 503
    assert 'private connection' not in result.text
