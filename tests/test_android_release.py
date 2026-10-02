"""Release preflight protects distributable builds, not live application data."""
import base64
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def release():
    path = ROOT / 'scripts/build_android_release.py'
    assert path.exists(), 'Release preflight is missing'
    spec = importlib.util.spec_from_file_location('android_release', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def config(url='https://project.supabase.co', key='sb_publishable_test-only'):
    return {'SUPABASE_URL': url, 'SUPABASE_ANON_KEY': key}


def test_release_accepts_public_client_configuration():
    assert release().validate_client_config(config()) == 'https://project.supabase.co'


@pytest.mark.parametrize('url', ['http://project.supabase.co', 'https://example.supabase.co', 'https://localhost', 'https://user:pass@project.supabase.co', 'https://project.supabase.co/path'])
def test_release_rejects_placeholder_and_invalid_backend_origins(url):
    with pytest.raises(ValueError):
        release().validate_client_config(config(url))


def test_release_rejects_server_credentials_and_missing_values():
    payload = base64.urlsafe_b64encode(json.dumps({'role': 'service_role'}).encode()).decode().rstrip('=')
    for key in ('', 'sb_secret_test-only', 'header.' + payload + '.signature'):
        with pytest.raises(ValueError):
            release().validate_client_config(config(key=key))


def test_release_rejects_debug_signer_and_wrong_fingerprint():
    m = release()
    for info in ['Signer #1 certificate DN: CN=Android Debug\nSigner #1 certificate SHA-256 digest: ' + 'a'*64,
                 'Signer #1 certificate SHA-256 digest: ' + 'b'*64]:
        with pytest.raises(ValueError):
            m.validate_signer(info, 'a'*64)
    m.validate_signer('Signer #1 certificate DN: CN=CitizenFlood release\nSigner #1 certificate SHA-256 digest: ' + 'a'*64, 'a'*64)
