"""Liveness is separate from dependency readiness; no private diagnostics leave HTTP."""
from fastapi import APIRouter
from sqlalchemy import text
from ..db.session import engine
from ..http.errors import ApiError

router = APIRouter()


def check_database():
    with engine.connect() as connection:
        connection.execute(text("SET LOCAL statement_timeout = '2000ms'"))
        connection.execute(text('SELECT version_num FROM alembic_version')).scalar_one()
        connection.execute(text('SELECT id FROM plants LIMIT 0'))


@router.get('/ready', tags=['operations'])
def ready():
    try:
        check_database()
    except Exception:
        raise ApiError(503, 'not_ready', 'Backend dependencies are unavailable')
    return {'status': 'ready'}
