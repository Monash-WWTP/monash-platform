from fastapi.testclient import TestClient
from sqlalchemy import inspect
from alembic import command
from alembic.config import Config
from pathlib import Path

from app.db.models import Base
from app.db.session import engine
from app.main import app
from app.seed import seed


def test_startup_does_not_create_schema_or_fetch_seed(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("startup must not mutate schema or fetch remote data")

    monkeypatch.setattr(Base.metadata, "create_all", forbidden)
    monkeypatch.setattr(seed, "seed_if_empty", forbidden)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.downgrade(config, "base")
    try:
        with TestClient(app) as client:
            assert client.get("/api/v1/health").status_code == 200
        assert not (set(inspect(engine).get_table_names()) & set(Base.metadata.tables))
    finally:
        command.upgrade(config, "head")
