import json

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app import operator_auth


def _credentials(token: str = "test-session") -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_operator_auth_requires_bearer_credentials():
    with pytest.raises(HTTPException) as exc:
        operator_auth.require_operator(None)

    assert exc.value.status_code == 401


def test_operator_auth_fails_closed_without_allowlist(monkeypatch):
    monkeypatch.setattr(operator_auth.settings, "wwtp_operator_emails", "")

    def unexpected_auth_request(*_args, **_kwargs):
        pytest.fail("Auth service must not be called without an operator allowlist")

    monkeypatch.setattr(operator_auth, "urlopen", unexpected_auth_request)
    with pytest.raises(HTTPException) as exc:
        operator_auth.require_operator(_credentials())

    assert exc.value.status_code == 503


def test_operator_auth_accepts_confirmed_allowlisted_user(monkeypatch):
    monkeypatch.setattr(operator_auth.settings, "wwtp_operator_emails", "Operator@Example.com")

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps({
                "email": "operator@example.com",
                "email_confirmed_at": "2026-09-28T00:00:00Z",
            }).encode()

    monkeypatch.setattr(operator_auth, "urlopen", lambda *_args, **_kwargs: Response())

    assert operator_auth.require_operator(_credentials()) == "operator@example.com"
