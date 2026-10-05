"""Liveness is separate from migrated-schema readiness; private diagnostics stay inside."""
from pathlib import Path
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import APIRouter
from sqlalchemy import text
from ..db.session import engine
from ..http.errors import ApiError
router=APIRouter()
EXPECTED_REVISION=ScriptDirectory.from_config(Config(str(Path(__file__).resolve().parents[2]/'alembic.ini'))).get_current_head()


def check_database():
    with engine.connect() as connection:
        connection.execute(text("SET LOCAL statement_timeout = '2000ms'"))
        revision=connection.execute(text('SELECT version_num FROM alembic_version')).scalar_one()
        if revision!=EXPECTED_REVISION:raise ValueError('Schema does not match this release')
        connection.execute(text('SELECT id FROM plants LIMIT 0'))


@router.get('/ready',tags=['operations'])
def ready():
    try:check_database()
    except Exception:raise ApiError(503,'not_ready','Backend dependencies are unavailable')
    return {'status':'ready'}
