"""Release preflight protects distributable builds, not live application data."""

import base64
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def release():
    path = ROOT / "scripts/build_android_release.py"
    assert path.exists(), "Release preflight is missing"
    spec = importlib.util.spec_from_file_location("android_release", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def config(url="https://api.monash.test"):
    return {
        "API_BASE_URL": url,
        "OIDC_ISSUER": "https://identity.monash.test/",
        "OIDC_DISCOVERY_URL": "https://identity.monash.test/application/o/citizen-mobile/.well-known/openid-configuration",
        "OIDC_CLIENT_ID": "citizen-mobile",
        "LOCAL_STAGING": False,
    }


def test_release_accepts_public_client_configuration():
    assert release().validate_client_config(config()) == "https://api.monash.test"


@pytest.mark.parametrize(
    "url",
    [
        "http://api.monash.test",
        "https://localhost",
        "https://127.0.0.1",
        "https://user:pass@api.monash.test",
        "https://api.monash.test/path",
        "https://example.com",
    ],
)
def test_release_rejects_placeholder_and_invalid_backend_origins(url):
    with pytest.raises(ValueError):
        release().validate_client_config(config(url))


def test_release_rejects_server_credentials_and_missing_values():
    for changes in (
        {"OIDC_CLIENT_SECRET": "secret"},
        {"SUPABASE_ANON_KEY": "obsolete"},
        {"LOCAL_STAGING": True},
        {"OIDC_ISSUER": ""},
        {"OIDC_DISCOVERY_URL": "http://localhost:9100/"},
        {"OIDC_CLIENT_ID": ""},
        {"OIDC_DISCOVERY_URL": "https://attacker.test/config"},
    ):
        with pytest.raises(ValueError):
            release().validate_client_config({**config(), **changes})


def test_release_rejects_debug_signer_and_wrong_fingerprint():
    m = release()
    for info in [
        "Signer #1 certificate DN: CN=Android Debug\nSigner #1 certificate SHA-256 digest: "
        + "a" * 64,
        "Signer #1 certificate SHA-256 digest: " + "b" * 64,
    ]:
        with pytest.raises(ValueError):
            m.validate_signer(info, "a" * 64)
    m.validate_signer(
        "Signer #1 certificate DN: CN=CitizenFlood release\nSigner #1 certificate SHA-256 digest: "
        + "a" * 64,
        "a" * 64,
    )
