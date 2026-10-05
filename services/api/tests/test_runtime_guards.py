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
