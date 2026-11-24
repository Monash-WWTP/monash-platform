"""Operator sign-in forces a fresh MFA login with max_age, not prompt=login."""

from datetime import timedelta
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from app.db.platform import LoginAttempt, now
from app.db.session import SessionLocal
from app.identity.dependencies import digest
from app.main import app
from app.routers import auth


def metadata():
    return {
        "authorization_endpoint": "https://identity.invalid/authorize",
        "token_endpoint": "https://identity.invalid/token",
        "jwks_uri": "https://identity.invalid/keys",
    }


@pytest.mark.parametrize("operator", [True, False])
def test_login_redirect_requests_recent_login_only_for_operators(monkeypatch, operator):
    monkeypatch.setattr(auth, "discovery", metadata)
    r = TestClient(app).get(
        "/api/v1/auth/login",
        params={"operator": str(operator).lower()},
        follow_redirects=False,
    )
    assert r.status_code == 303
    query = parse_qs(urlparse(r.headers["location"]).query)
    assert "prompt" not in query
    if operator:
        assert query["max_age"] == [str(auth.OPERATOR_MAX_AGE)]
    else:
        assert "max_age" not in query


def callback(monkeypatch, claims):
    state, browser, nonce = str(uuid4()), str(uuid4()), str(uuid4())
    with SessionLocal() as db:
        db.add(
            LoginAttempt(
                state_hash=digest(state),
                browser_hash=digest(browser),
                operator_login=True,
                verifier="test-verifier",
                nonce=nonce,
                expires_at=now() + timedelta(minutes=5),
            )
        )
        db.commit()
    monkeypatch.setattr(auth, "discovery", metadata)
    monkeypatch.setattr(
        auth.httpx,
        "post",
        lambda *a, **k: httpx.Response(
            200,
            json={"id_token": "test-token"},
            request=httpx.Request("POST", "https://identity.invalid/token"),
        ),
    )
    monkeypatch.setattr(
        auth,
        "signing_keys",
        lambda _: SimpleNamespace(
            get_signing_key_from_jwt=lambda _: SimpleNamespace(key="test-key")
        ),
    )
    monkeypatch.setattr(
        auth, "validate_token", lambda *a, **k: {"nonce": nonce, **claims}
    )
    monkeypatch.setattr(
        auth,
        "account_from_claims",
        lambda db, c: pytest.fail("stale operator login must not create a session"),
    )
    client = TestClient(app, base_url="https://testserver")
    client.cookies.set("monash_login", browser)
    return client.get(
        "/api/v1/auth/callback",
        params={"code": "test-code", "state": state},
        follow_redirects=False,
    )


STALE = auth.OPERATOR_MAX_AGE + auth.CLOCK_SKEW + 60


@pytest.mark.parametrize(
    "auth_time",
    [
        lambda t: None,  # missing
        lambda t: str(int(t)),  # wrong type
        lambda t: True,  # bool is not a timestamp
        lambda t: int(t) + 3600,  # future
        lambda t: int(t) - STALE,  # older than max_age
    ],
)
def test_operator_callback_rejects_missing_or_stale_auth_time(monkeypatch, auth_time):
    value = auth_time(now().timestamp())
    claims = {"amr": ["pwd", "mfa"]}
    if value is not None:
        claims["auth_time"] = value
    assert callback(monkeypatch, claims).status_code == 401


def test_fresh_operator_login_window():
    t = now().timestamp()
    assert auth.fresh_operator_login(t)
    assert auth.fresh_operator_login(t - auth.OPERATOR_MAX_AGE)
    assert not auth.fresh_operator_login(
        t - auth.OPERATOR_MAX_AGE - auth.CLOCK_SKEW - 5
    )
    assert not auth.fresh_operator_login(None)
