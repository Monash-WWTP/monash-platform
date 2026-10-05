from uuid import uuid4
import pytest
from app.db.platform import Account, AuditEvent, BrowserSession
from app.db.session import SessionLocal
from app.identity.administration import set_capabilities


def test_grant_uses_stable_account_and_audits_then_revokes_sessions():
    with SessionLocal() as db:
        target = Account(
            issuer="https://identity.test/",
            subject=str(uuid4()),
            email="verified@example.test",
        )
        db.add(target)
        db.commit()
        db.refresh(target)
        with pytest.raises(ValueError):
            set_capabilities(
                db,
                "verified@example.test",
                ["report:review"],
                "local-admin",
                "approved invitation",
            )
        with pytest.raises(ValueError):
            set_capabilities(
                db, target.id, ["unknown"], "local-admin", "approved invitation"
            )
        set_capabilities(
            db,
            target.id,
            ["report:own", "report:review"],
            "local-admin",
            "approved invitation",
        )
        assert target.capabilities == ["report:own", "report:review"]
        event = (
            db.query(AuditEvent)
            .filter_by(resource_id=target.id, action="account.capabilities")
            .one()
        )
        assert event.details["administrator"] == "local-admin"
        assert event.details["before"] == ["report:own"]
        assert db.query(BrowserSession).filter_by(account_id=target.id).count() == 0
