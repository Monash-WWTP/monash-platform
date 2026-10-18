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


def test_schema_revision_mismatch_is_not_ready(monkeypatch):
    from app.routers import readiness
    monkeypatch.setattr(readiness,'EXPECTED_REVISION','unavailable-new-release',raising=False)
    assert TestClient(app).get('/api/v1/ready').status_code==503


def test_configured_private_storage_outage_is_not_ready(monkeypatch):
    from app.config import settings
    from app.reporting import storage
    monkeypatch.setattr(settings, 'storage_endpoint', 'https://storage.fixture.invalid')

    class UnavailableStorage:
        def head_bucket(self, **kwargs):
            raise OSError('private storage credential details')

    monkeypatch.setattr(storage, 'client', lambda **kwargs: UnavailableStorage())
    result = TestClient(app).get('/api/v1/ready')
    assert result.status_code == 503
    assert 'private storage' not in result.text
    assert TestClient(app).get('/api/v1/health').status_code == 200


def test_configured_identity_outage_is_not_ready(monkeypatch):
    import httpx
    from app.config import settings
    monkeypatch.setattr(settings, 'oidc_jwks_url', 'https://identity.fixture.invalid/jwks')

    def unavailable(*args, **kwargs):
        raise OSError('private identity connection details')

    monkeypatch.setattr(httpx, 'get', unavailable)
    result = TestClient(app).get('/api/v1/ready')
    assert result.status_code == 503
    assert 'private identity' not in result.text


def test_configured_dependencies_must_be_usable(monkeypatch):
    import httpx
    from app.config import settings
    from app.reporting import storage
    monkeypatch.setattr(settings, 'storage_endpoint', 'https://storage.fixture.invalid')
    monkeypatch.setattr(settings, 'oidc_jwks_url', 'https://identity.fixture.invalid/jwks')
    checked_buckets = []

    class AvailableStorage:
        def head_bucket(self, **kwargs):
            checked_buckets.append(kwargs['Bucket'])

    monkeypatch.setattr(storage, 'client', lambda **kwargs: AvailableStorage())
    request = httpx.Request('GET', settings.oidc_jwks_url)
    monkeypatch.setattr(httpx, 'get', lambda *args, **kwargs: httpx.Response(
        200, json={'keys': [{'kty': 'RSA', 'kid': 'fixture'}]}, request=request))
    assert TestClient(app).get('/api/v1/ready').status_code == 200
    assert checked_buckets == [settings.storage_bucket]
    monkeypatch.setattr(httpx, 'get', lambda *args, **kwargs: httpx.Response(
        200, json={'keys': []}, request=request))
    assert TestClient(app).get('/api/v1/ready').status_code == 503
