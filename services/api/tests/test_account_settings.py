import hashlib
import hmac
import json
import time
from datetime import UTC, datetime
from uuid import uuid4

from app.config import settings
from app.db.platform import Account
from app.db.session import SessionLocal
from app.identity.dependencies import account_from_claims, require_account
from app.main import app
from fastapi.testclient import TestClient
from test_reporting import account

client = TestClient(app)


def test_trusted_settings_links_fail_closed_and_display_name_provenance(monkeypatch):
    a = account(["report:own"])
    app.dependency_overrides[require_account] = lambda: a
    try:
        monkeypatch.setattr(settings, "account_settings_enabled", False)
        assert client.get("/api/v1/auth/account-settings").json()["available"] is False
        monkeypatch.setattr(settings, "account_settings_enabled", True)
        monkeypatch.setattr(settings, "oidc_issuer", "https://accounts.example.test/")
        links = client.get("/api/v1/auth/account-settings").json()
        assert links["available"] is True
        assert (
            links["actions"]["profile"]
            == "https://accounts.example.test/if/flow/monash-account-profile/"
        )
        assert "/admin" not in json.dumps(links)
        monkeypatch.setattr(settings, "oidc_issuer", "http://accounts.example.test/")
        assert client.get("/api/v1/auth/account-settings").json()["available"] is False
        with SessionLocal() as db:
            c = {
                "iss": a.issuer,
                "sub": a.subject,
                "email": a.email,
                "iat": int(time.time()),
                "name": "  Research volunteer  ",
            }
            assert account_from_claims(db, c).display_name == "Research volunteer"
            assert (
                account_from_claims(
                    db, {**c, "iat": c["iat"] - 1, "name": "Old label"}
                ).display_name
                == "Research volunteer"
            )
            assert (
                account_from_claims(
                    db, {**c, "iat": c["iat"] + 1, "name": {"bad": "object"}}
                ).display_name
                is None
            )
    finally:
        app.dependency_overrides.clear()


def test_account_change_events_preserve_identity_and_revoke_old_proofs(monkeypatch):
    monkeypatch.setattr(settings, "identity_event_secret", "qa-event-secret")
    a = account(["report:own", "report:respond"])
    monkeypatch.setattr(settings, "oidc_issuer", a.issuer)
    for action in ["account.email_changed", "credentials.changed", "sessions.revoked"]:
        raw = json.dumps(
            {
                "id": str(uuid4()),
                "issuer": a.issuer,
                "subject": a.subject,
                "occurred_at": datetime.now(UTC).isoformat(),
                "action": action,
            }
        ).encode()
        signature = hmac.new(
            settings.identity_event_secret.encode(), raw, hashlib.sha256
        ).hexdigest()
        r = client.post(
            "/api/v1/identity/events",
            content=raw,
            headers={"X-Monash-Signature": signature},
        )
        assert r.status_code == 204, r.text
        assert (
            client.post(
                "/api/v1/identity/events",
                content=raw,
                headers={"X-Monash-Signature": signature},
            ).status_code
            == 204
        )
        with SessionLocal() as db:
            current = db.get(Account, a.id)
            assert current.subject == a.subject and current.email == a.email
            assert current.capabilities == ["report:own", "report:respond"]
            assert current.revoked_before is not None
