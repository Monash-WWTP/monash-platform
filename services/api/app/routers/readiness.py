"""Check schema and configured dependencies; keep private diagnostics inside."""
from pathlib import Path
import httpx
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import APIRouter
from sqlalchemy import text
from ..db.session import engine
from ..http.errors import ApiError
from ..config import settings
from ..identity.network import network_url, network_headers
from ..reporting import storage
router=APIRouter()
EXPECTED_REVISION=ScriptDirectory.from_config(Config(str(Path(__file__).resolve().parents[2]/'alembic.ini'))).get_current_head()


def check_database():
    with engine.connect() as connection:
        connection.execute(text("SET LOCAL statement_timeout = '2000ms'"))
        revision=connection.execute(text('SELECT version_num FROM alembic_version')).scalar_one()
        if revision!=EXPECTED_REVISION:raise ValueError('Schema does not match this release')
        connection.execute(text('SELECT id FROM plants LIMIT 0'))


def check_storage():
    if settings.storage_endpoint:
        storage.client(timeout=2, retries=0).head_bucket(Bucket=settings.storage_bucket)


def check_identity():
    if settings.oidc_jwks_url:
        result = httpx.get(network_url(settings.oidc_jwks_url),
                           headers=network_headers(), timeout=2)
        result.raise_for_status()
        if not result.json().get('keys'):
            raise ValueError('Identity signing keys are unavailable')


@router.get('/ready',tags=['operations'])
def ready():
    try:
        check_database()
        check_storage()
        check_identity()
    except Exception:raise ApiError(503,'not_ready','Backend dependencies are unavailable')
    return {'status':'ready'}
