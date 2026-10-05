"""Signed private identity events invalidate application-held sessions and old proofs."""

import hashlib, hmac
from datetime import datetime, timezone, timedelta
from typing import Literal
from uuid import UUID
from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from ..config import settings
from ..db.session import get_db
from ..db.platform import Account, BrowserSession, AuditEvent
from ..http.errors import ApiError

router = APIRouter(prefix="/identity", tags=["identity events"])


class IdentityEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    issuer: str
    subject: str
    occurred_at: datetime
    action: Literal["credentials.reset", "account.disabled"]


@router.post("/events", status_code=204)
async def event(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    if not settings.identity_event_secret:
        raise ApiError(
            503,
            "identity_events_unavailable",
            "Identity event verification is unavailable",
        )
    signature = hmac.new(
        settings.identity_event_secret.encode(), raw, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(
        signature, request.headers.get("X-Monash-Signature", "")
    ):
        raise ApiError(401, "invalid_identity_event", "Invalid identity event proof")
    try:
        body = IdentityEvent.model_validate_json(raw)
    except ValueError:
        raise ApiError(422, "invalid_identity_event", "Malformed identity event")
    if (
        body.issuer != settings.oidc_issuer
        or not body.subject
        or body.occurred_at.tzinfo is None
        or abs(datetime.now(timezone.utc) - body.occurred_at) > timedelta(minutes=5)
    ):
        raise ApiError(
            401, "invalid_identity_event", "Identity event origin or time is invalid"
        )
    if db.get(AuditEvent, str(body.id)):
        return Response(status_code=204)
    account = (
        db.query(Account)
        .filter_by(issuer=body.issuer, subject=body.subject)
        .with_for_update()
        .first()
    )
    if account:
        account.revoked_before = max(
            filter(None, [account.revoked_before, body.occurred_at])
        )
        db.query(BrowserSession).filter_by(account_id=account.id).delete()
        if body.action == "account.disabled":
            account.capabilities = []
    resource = hashlib.sha256((body.issuer + "\0" + body.subject).encode()).hexdigest()
    db.add(
        AuditEvent(
            id=str(body.id),
            actor_id=None,
            action="identity." + body.action,
            resource_id=resource,
            details={
                "occurred_at": body.occurred_at.isoformat(),
                "account_id": account.id if account else None,
            },
        )
    )
    db.commit()
    return Response(status_code=204)
