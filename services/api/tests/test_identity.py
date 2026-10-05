import time
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from app.identity.tokens import validate_token


@pytest.fixture
def signer():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def claims(**changes):
    return {
        "iss": "http://localhost:9100/application/o/citizen/",
        "aud": "citizen-mobile",
        "sub": "stable-subject",
        "exp": int(time.time()) + 60,
        "iat": int(time.time()),
        "email": "citizen@example.com",
        "email_verified": True,
        **changes,
    }


def test_verified_identity(signer):
    token = jwt.encode(claims(), signer, algorithm="RS256")
    result = validate_token(
        token, signer.public_key(), claims()["iss"], ["citizen-mobile"]
    )
    assert result["sub"] == "stable-subject"


@pytest.mark.parametrize(
    "changes",
    [
        {"iss": "https://attacker.invalid"},
        {"aud": "other-app"},
        {"exp": int(time.time()) - 60},
        {"email_verified": False},
        {"sub": ""},
    ],
)
def test_invalid_proof_fails_closed(signer, changes):
    token = jwt.encode(claims(**changes), signer, algorithm="RS256")
    with pytest.raises(ValueError):
        validate_token(token, signer.public_key(), claims()["iss"], ["citizen-mobile"])


def test_wrong_signer_rejected(signer):
    token = jwt.encode(
        claims(),
        rsa.generate_private_key(public_exponent=65537, key_size=2048),
        algorithm="RS256",
    )
    with pytest.raises(ValueError):
        validate_token(token, signer.public_key(), claims()["iss"], ["citizen-mobile"])


def test_operator_capability_requires_mfa():
    from app.identity.dependencies import require_mfa
    from app.db.platform import Account
    from app.http.errors import ApiError

    item = Account(capabilities=["scenario:operate"])
    with pytest.raises(ApiError):
        require_mfa(item)
    item._mfa_verified = True
    require_mfa(item)


def test_recovery_event_signature_revokes_account_proof():
    import hashlib, hmac, json
    from datetime import datetime, timezone
    from uuid import uuid4
    from fastapi.testclient import TestClient
    from app.main import app
    from app.config import settings
    from app.db.session import SessionLocal
    from app.db.platform import Account

    old = (
        settings.identity_event_secret
        if hasattr(settings, "identity_event_secret")
        else ""
    )
    try:
        settings.identity_event_secret = "isolated-test-event-secret"
        subject = str(uuid4())
        with SessionLocal() as db:
            account = Account(
                issuer=settings.oidc_issuer, subject=subject, email="qa@example.test"
            )
            db.add(account)
            db.commit()
            db.refresh(account)
            identifier = account.id
        body = json.dumps(
            {
                "id": str(uuid4()),
                "issuer": settings.oidc_issuer,
                "subject": subject,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "action": "credentials.reset",
            },
            separators=(",", ":"),
        ).encode()
        client = TestClient(app)
        assert (
            client.post(
                "/api/v1/identity/events",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Monash-Signature": "wrong",
                },
            ).status_code
            == 401
        )
        signature = hmac.new(
            settings.identity_event_secret.encode(), body, hashlib.sha256
        ).hexdigest()
        assert (
            client.post(
                "/api/v1/identity/events",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Monash-Signature": signature,
                },
            ).status_code
            == 204
        )
        with SessionLocal() as db:
            assert db.get(Account, identifier).revoked_before is not None
    finally:
        settings.identity_event_secret = old
