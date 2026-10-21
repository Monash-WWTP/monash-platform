"""Signed private identity events invalidate application-held sessions and old proofs."""

import hashlib, hmac
from datetime import datetime, timezone, timedelta
from typing import Literal
from uuid import UUID, uuid4
from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import text
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
    action: Literal[
        "credentials.reset",
        "account.disabled",
        "account.email_changed",
        "credentials.changed",
        "sessions.revoked",
    ]


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
    resource = hashlib.sha256((body.issuer + "\0" + body.subject).encode()).hexdigest()
    # Serialize event-ID retries, including identities not yet projected into accounts.
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:resource, 0))"),
        {"resource": resource},
    )
    original = db.get(AuditEvent, str(body.id))
    if original:
        if (
            original.action != "identity." + body.action
            or original.resource_id != resource
        ):
            raise ApiError(
                409,
                "identity_event_collision",
                "Event identity does not match its original delivery",
            )
        deliveries = (
            db.query(AuditEvent)
            .filter(
                AuditEvent.resource_id == resource, AuditEvent.action == original.action
            )
            .all()
        )
        previous = max(
            datetime.fromisoformat(e.details["occurred_at"])
            for e in deliveries
            if e.id == str(body.id)
            or e.details.get("delivery_event_id") == str(body.id)
        )
        if body.occurred_at <= previous:
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
            id=str(uuid4()) if original else str(body.id),
            actor_id=None,
            action="identity." + body.action,
            resource_id=resource,
            details={
                "occurred_at": body.occurred_at.isoformat(),
                "delivery_event_id": str(body.id),
                "account_id": account.id if account else None,
            },
        )
    )
    db.commit()
    return Response(status_code=204)
