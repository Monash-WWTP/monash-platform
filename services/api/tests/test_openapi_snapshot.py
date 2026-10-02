import json
from pathlib import Path

from alembic.runtime.migration import MigrationContext

from app.db.session import engine
from app.main import app


SNAPSHOT = Path(__file__).resolve().parents[1] / "openapi.json"


def test_openapi_snapshot_matches_running_contract():
    assert SNAPSHOT.read_text() == json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"


def test_disposable_database_is_at_initial_revision():
    with engine.connect() as connection:
        assert MigrationContext.configure(connection).get_current_revision() == "0001_initial"
