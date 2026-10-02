"""Smoke test for the installed monorepo Python package boundaries."""

from importlib.util import find_spec
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[3]


def test_workspace_import_paths_and_offline_health(monkeypatch):
    api_spec = find_spec("app")
    sim_spec = find_spec("wwtp_sim")
    assert api_spec is not None
    assert sim_spec is not None
    assert Path(api_spec.origin).resolve().is_relative_to(ROOT / "services/api/app")
    assert Path(sim_spec.origin).resolve().is_relative_to(ROOT / "packages/simulation/wwtp_sim")

    from app.db.models import Base
    from app.main import app
    from app.seed import seed

    def forbidden(*args, **kwargs):
        raise AssertionError("health must not create schema or fetch legacy seed data")

    monkeypatch.setattr(Base.metadata, "create_all", forbidden)
    monkeypatch.setattr(seed, "_fetch", forbidden)
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
