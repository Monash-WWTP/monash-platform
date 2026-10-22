import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import Settings


def test_production_rejects_insecure_or_incomplete_identity():
    with pytest.raises(ValueError):
        Settings(database_url="postgresql://test", app_env="production")
    with pytest.raises(ValueError):
        Settings(
            database_url="postgresql://test",
            app_env="production",
            auth_mode="oidc",
            session_secure=False,
        )


def test_request_limit_precedes_multipart_parsing():
    response = TestClient(app).post(
        "/api/v1/media", headers={"Content-Length": str(12 * 1024 * 1024)}, content=b"x"
    )
    assert response.status_code == 413
    assert response.headers["x-content-type-options"] == "nosniff"


def test_oversized_request_preserves_error_contract_and_correlation():
    response = TestClient(app).post(
        "/api/v1/media", headers={"Content-Length": str(12 * 1024 * 1024)}, content=b"x"
    )
    assert response.status_code == 413
    error = response.json()["error"]
    assert error["request_id"]
    assert response.headers["x-request-id"] == error["request_id"]


def production_settings(**changes):
    values = dict(database_url="postgresql://test", app_env="production",
                  identity_event_secret="synthetic-event-secret",
                  oidc_client_secret="synthetic-client-secret",
                  oidc_issuer="https://accounts.example.test/",
                  oidc_discovery_url="https://accounts.example.test/discovery",
                  oidc_jwks_url="https://accounts.example.test/jwks",
                  web_origin="https://web.example.test",
                  oidc_callback_url="https://web.example.test/api/v1/auth/callback",
                  cors_origins="https://web.example.test",
                  storage_endpoint="https://storage.example.test",
                  storage_access_key="synthetic-key", storage_secret_key="synthetic-secret")
    values.update(changes)
    return Settings(**values)


def test_complete_secure_production_configuration_is_accepted():
    assert production_settings().app_env == "production"
    assert production_settings(oidc_backchannel_origin="https://identity.internal").app_env == "production"


@pytest.mark.parametrize('changes', [
    {'storage_endpoint': 'http://storage.example.test'},
    {'storage_endpoint': 'https://user:password@storage.example.test'},
    {'web_origin': 'https://web.example.test/path'},
    {'oidc_callback_url': 'https://other.example.test/api/v1/auth/callback'},
    {'cors_origins': 'http://web.example.test'},
    {'oidc_backchannel_origin': 'http://identity-server:9000'},
])
def test_production_rejects_unsafe_service_urls(changes):
    with pytest.raises(ValueError):
        production_settings(**changes)
