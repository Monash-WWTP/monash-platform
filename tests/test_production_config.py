"""Render deployment configuration with synthetic inputs; never start services."""

import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = ROOT / 'infra/production'
SYNTHETIC = {
    'API_IMAGE': 'registry.example/monash@sha256:' + 'a' * 64,
    'CADDY_IMAGE': 'caddy@sha256:' + 'b' * 64,
    'API_DOMAIN': 'api.example.invalid',
    'WEB_ORIGIN': 'https://water.example.invalid',
    'OIDC_CALLBACK_URL': 'https://water.example.invalid/api/v1/auth/callback',
    'IDENTITY_DOMAIN': 'accounts.example.invalid',
    'APP_DB_PASSWORD': 'synthetic-app-password',
    'IDENTITY_DB_PASSWORD': 'synthetic-identity-password',
    'IDENTITY_SECRET': 'synthetic-identity-secret',
    'IDENTITY_EVENT_SECRET': 'synthetic-event-secret',
    'OIDC_ISSUER': 'https://accounts.example.invalid/',
    'OIDC_DISCOVERY_URL': 'https://accounts.example.invalid/application/o/monash-web/.well-known/openid-configuration',
    'OIDC_JWKS_URL': 'https://accounts.example.invalid/application/o/monash-web/jwks/',
    'OIDC_CLIENT_SECRET': 'synthetic-client-secret',
    'STORAGE_ENDPOINT': 'https://private-s3.example.invalid',
    'STORAGE_ACCESS_KEY': 'synthetic-storage-access',
    'STORAGE_SECRET_KEY': 'synthetic-storage-secret',
    'STORAGE_BUCKET': 'synthetic-private-photos',
    'STORAGE_REGION': 'synthetic-region',
    'SMTP_HOST': 'smtp.example.invalid',
    'SMTP_PORT': '587',
    'SMTP_USERNAME': 'synthetic-mail-user',
    'SMTP_PASSWORD': 'synthetic-mail-password',
    'SMTP_FROM': 'accounts@example.invalid',
}


def render(**overrides):
    if not shutil.which('docker'):
        pytest.skip('Docker Compose is required to render production configuration')
    env = {key: value for key, value in os.environ.items() if key not in SYNTHETIC}
    env.update(SYNTHETIC)
    env.update(overrides)
    return subprocess.run(
        ['docker', 'compose', '--env-file', '/dev/null', '-f', str(PRODUCTION / 'compose.yaml'),
         '--profile', 'release', 'config', '--format', 'json'],
        env=env, text=True, capture_output=True,
    )


def test_production_render_has_private_internal_services_and_independent_tls_startup():
    result = render()
    assert result.returncode == 0, result.stderr
    services = json.loads(result.stdout)['services']
    assert set(services) == {'database', 'identity-db', 'identity-server', 'identity-worker', 'migrate', 'api', 'caddy'}
    for name, service in services.items():
        if name != 'caddy':
            assert not service.get('ports'), name
        assert service['logging']['driver'] == 'local'
    assert {port['published'] for port in services['caddy']['ports']} == {'80', '443'}
    assert not services['caddy'].get('depends_on'), 'TLS/identity must start independently of API readiness'
    api = services['api']['environment']
    assert api['APP_ENV'] == 'production'
    assert api['SESSION_SECURE'] == 'true'
    assert api['IDENTITY_EVENT_SECRET'] == SYNTHETIC['IDENTITY_EVENT_SECRET']
    assert api['OIDC_ISSUER'] == SYNTHETIC['OIDC_ISSUER']
    assert api['STORAGE_ENDPOINT'] == SYNTHETIC['STORAGE_ENDPOINT']
    assert services['database']['image'] == 'postgres:16.13'
    assert services['identity-server']['image'] == 'ghcr.io/goauthentik/server:2026.8.3'
    assert services['api']['depends_on']['migrate']['condition'] == 'service_completed_successfully'


@pytest.mark.parametrize('name', list(SYNTHETIC))
def test_production_render_rejects_missing_required_inputs(name):
    result = render(**{name: ''})
    assert result.returncode != 0
    assert name in result.stderr
