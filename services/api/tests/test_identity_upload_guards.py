"""Configuration and request-isolation regressions; no database or storage access."""

import asyncio
from io import BytesIO
from threading import Event
from types import SimpleNamespace

import httpx
from PIL import Image
import pytest

from app.config import Settings
from app.db.session import get_db
from app.identity.dependencies import require_citizen
from app.main import app
from app.reporting import storage


def production_settings(**overrides):
    return Settings(
        **{
            'database_url': 'postgresql://unused',
            'app_env': 'production',
            'oidc_issuer': 'https://identity.example/',
            'oidc_discovery_url': 'https://identity.example/discovery',
            'oidc_jwks_url': 'https://identity.example/jwks',
            'oidc_client_secret': 'synthetic-client-secret',
            'oidc_callback_url': 'https://water.example/api/v1/auth/callback',
            'web_origin': 'https://water.example',
            'storage_endpoint': 'https://storage.example',
            'storage_access_key': 'synthetic',
            'storage_secret_key': 'synthetic',
            'identity_event_secret': 'synthetic-revocation-secret',
            **overrides,
        }
    )


@pytest.mark.parametrize('secret', ['', '   '])
def test_production_requires_security_event_verification(secret):
    with pytest.raises(ValueError, match='identity_event_secret'):
        production_settings(identity_event_secret=secret)


def test_distinct_mobile_issuer_fails_configuration_instead_of_every_login():
    with pytest.raises(ValueError, match='shared issuer'):
        production_settings(oidc_mobile_issuer='https://mobile.example/')


def test_shared_mobile_issuer_and_revocation_secret_are_supported():
    production_settings(oidc_mobile_issuer='https://identity.example/')


def test_slow_photo_storage_does_not_block_independent_requests(monkeypatch):
    started, release = Event(), Event()

    class SlowStore:
        def put_object(self, **kwargs):
            started.set()
            release.wait(timeout=2)

    class FakeDatabase:
        def add(self, media):
            media.id = 'synthetic-media-id'

        def commit(self):
            pass

    stream = BytesIO()
    Image.new('RGB', (8, 8)).save(stream, format='PNG')
    monkeypatch.setattr(storage, 'client', lambda: SlowStore())
    app.dependency_overrides[get_db] = lambda: FakeDatabase()
    app.dependency_overrides[require_citizen] = lambda: SimpleNamespace(id='synthetic-owner')

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            upload = asyncio.create_task(client.post('/api/v1/media', files={'file': ('photo.png', stream.getvalue())}))
            try:
                async def await_started():
                    while not started.is_set():
                        await asyncio.sleep(0.001)
                await asyncio.wait_for(await_started(), timeout=1)
                # Storage must still be waiting when another request finishes.
                response = await asyncio.wait_for(client.get('/api/v1/health'), timeout=0.5)
                assert response.status_code == 200
                assert not upload.done(), 'The health request was delayed until photo storage finished'
            finally:
                release.set()
                result = await upload
            assert result.status_code == 201

    try:
        asyncio.run(exercise())
    finally:
        app.dependency_overrides.clear()
