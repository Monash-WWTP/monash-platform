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


def test_matching_event_retry_revokes_sessions_created_after_uncertain_delivery(
    monkeypatch,
):
    from datetime import timedelta
    from app.db.platform import BrowserSession, AuditEvent
    from app.identity.dependencies import digest

    monkeypatch.setattr(settings, "identity_event_secret", "qa-retry-secret")
    a = account(["report:own"])
    monkeypatch.setattr(settings, "oidc_issuer", a.issuer)
    event_id = str(uuid4())
    initial = datetime.now(UTC) - timedelta(seconds=20)
    body = {
        "id": event_id,
        "issuer": a.issuer,
        "subject": a.subject,
        "occurred_at": initial.isoformat(),
        "action": "account.email_changed",
    }

    def deliver(value):
        raw = json.dumps(value).encode()
        return client.post(
            "/api/v1/identity/events",
            content=raw,
            headers={
                "X-Monash-Signature": hmac.new(
                    settings.identity_event_secret.encode(), raw, hashlib.sha256
                ).hexdigest()
            },
        )

    assert deliver(body).status_code == 204
    with SessionLocal() as db:
        db.add(
            BrowserSession(
                token_hash=digest("qa-between-attempts" + uuid4().hex),
                account_id=a.id,
                csrf_hash=digest("qa-csrf"),
                expires_at=datetime.now(UTC) + timedelta(minutes=10),
                mfa_verified=False,
            )
        )
        db.commit()
    retried = datetime.now(UTC)
    assert deliver({**body, "occurred_at": retried.isoformat()}).status_code == 204
    with SessionLocal() as db:
        assert db.query(BrowserSession).filter_by(account_id=a.id).count() == 0
        assert db.get(Account, a.id).revoked_before >= retried
        assert db.get(AuditEvent, event_id) is not None
    assert deliver({**body, "subject": "another-subject"}).status_code == 409


def test_unknown_account_uses_greatest_occurrence_not_last_delivery(monkeypatch):
    from datetime import timedelta
    from app.db.platform import AuditEvent
    from app.http.errors import ApiError
    import pytest

    issuer = "https://unknown-qa.example.test/"
    subject = uuid4().hex
    resource = hashlib.sha256((issuer + "\0" + subject).encode()).hexdigest()
    latest = datetime.now(UTC) - timedelta(seconds=10)
    with SessionLocal() as db:
        db.add(
            AuditEvent(
                id=str(uuid4()),
                actor_id=None,
                action="identity.sessions.revoked",
                resource_id=resource,
                details={"occurred_at": latest.isoformat()},
            )
        )
        db.commit()
        db.add(
            AuditEvent(
                id=str(uuid4()),
                actor_id=None,
                action="identity.sessions.revoked",
                resource_id=resource,
                details={"occurred_at": (latest - timedelta(seconds=30)).isoformat()},
            )
        )
        db.commit()
        with pytest.raises(ApiError):
            account_from_claims(
                db,
                {
                    "iss": issuer,
                    "sub": subject,
                    "email": "qa@example.test",
                    "iat": int((latest - timedelta(seconds=5)).timestamp()),
                },
            )
