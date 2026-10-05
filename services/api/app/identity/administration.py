"""Trusted server administration, never a public self-assignment endpoint."""

from uuid import UUID
from sqlalchemy.orm import Session
from ..db.platform import Account, AuditEvent, BrowserSession

ALLOWED = {"report:own", "report:review", "monitor:read", "scenario:operate"}


def set_capabilities(
    db: Session,
    account_id: str,
    capabilities: list[str],
    administrator: str,
    reason: str,
):
    UUID(account_id)
    if not administrator.strip() or not reason.strip():
        raise ValueError("Administrator and approval reason are required")
    if set(capabilities) - ALLOWED:
        raise ValueError("Unknown capability")
    target = db.query(Account).filter_by(id=account_id).with_for_update().first()
    if not target or target.issuer.startswith("legacy:"):
        raise ValueError("Verified native account is required")
    before = list(target.capabilities)
    target.capabilities = sorted(set(capabilities))
    db.query(BrowserSession).filter_by(account_id=target.id).delete()
    db.add(
        AuditEvent(
            actor_id=None,
            action="account.capabilities",
            resource_id=target.id,
            details={
                "administrator": administrator.strip(),
                "reason": reason.strip(),
                "before": before,
                "after": target.capabilities,
            },
        )
    )
    db.commit()
