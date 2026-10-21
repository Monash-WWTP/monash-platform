"""V2 citizen observations; v1 routes deliberately exclude these records."""

import hashlib
import json
from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Literal
from ..db.session import get_db
from ..db.platform import CitizenReport, Media, AuditEvent, Station
from ..identity.dependencies import (
    require_account,
    require_citizen,
    require_reviewer,
    require_mfa,
)
from ..http.errors import ApiError
from ..http.contracts import Page, ReportView
from ..reporting.observations import (
    ObservationInput,
    ObservationView,
    PublicObservation,
    WaterReading,
    PROTOCOL_ID,
    REVISION,
)
from ..reporting.schemas import ModerationInput

router = APIRouter(tags=["versioned citizen observations"])
PREFIX = "v2:"


class LegacyObservationView(ReportView):
    protocol_id: Literal["legacy-unspecified"]
    protocol_revision: Literal[0]


def query_v2(db):
    return db.query(CitizenReport).filter(CitizenReport.category.startswith(PREFIX))


def project(db, r):
    event = (
        db.query(AuditEvent)
        .filter_by(action="report.moderate", resource_id=r.id)
        .order_by(AuditEvent.created_at.desc())
        .first()
    )
    return {
        **r.payload,
        "id": r.id,
        "media_id": r.media_id,
        "moderation_status": r.status,
        "review_reason": event.details.get("reason") if event else None,
        "created_at": r.created_at,
    }


@router.get("/observation-protocols")
def protocols():
    return {
        "protocol_id": PROTOCOL_ID,
        "protocol_revision": REVISION,
        "supported_revisions": [1, 2],
        "types": [
            "flooding",
            "rain_occurrence",
            "water_appearance",
            "rainfall_accumulation",
            "water_reading",
            "temperature",
        ],
    }


@router.get("/observation-references")
def references(account=Depends(require_citizen), db: Session = Depends(get_db)):
    result = []
    for station in db.query(Station).all():
        ref = station.payload.get("stage_reference", {})
        if (
            ref.get("approved") is True
            and isinstance(ref.get("revision"), int)
            and ref["revision"] >= 1
            and ref.get("unit") == "m"
        ):
            result.append(
                {
                    "id": station.code,
                    "revision": ref["revision"],
                    "label": str(ref.get("label", station.code)),
                    "unit": "m",
                }
            )
    return {"items": result}


def validate_followup(db, account_id, body):
    previous_id = getattr(body, "previous_observation_id", None)
    if not previous_id:
        return
    previous = query_v2(db).filter_by(id=previous_id, owner_id=account_id).first()
    if (
        not previous
        or previous.payload.get("observation", {}).get("kind") != "flooding"
    ):
        raise ApiError(404, "report_not_found", "Observation not found")
    from datetime import datetime

    previous_time = datetime.fromisoformat(
        previous.payload["observed_at"].replace("Z", "+00:00")
    )
    if body.observed_at <= previous_time:
        raise ApiError(
            422, "invalid_followup", "Update must be observed after the earlier report"
        )
    if (
        body.latitude != previous.latitude
        or body.longitude != previous.longitude
        or body.location_source != "selected"
        or body.location_accuracy_m is not None
    ):
        raise ApiError(
            422,
            "invalid_followup",
            "Update must reuse the selected point without GPS accuracy",
        )


@router.post("/observations", status_code=201, response_model=ObservationView)
def create(
    body: ObservationInput,
    idempotency_key: str = Header(min_length=8, max_length=128),
    account=Depends(require_citizen),
    db: Session = Depends(get_db),
):
    payload = body.model_dump(mode="json")
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    previous = (
        db.query(CitizenReport)
        .filter_by(owner_id=account.id, idempotency_key=idempotency_key)
        .first()
    )
    if previous:
        if previous.payload_hash != digest or not previous.category.startswith(PREFIX):
            raise ApiError(
                409,
                "idempotency_conflict",
                "Retry key already used for different content",
            )
        return project(db, previous)
    validate_followup(db, account.id, body)
    if (
        isinstance(body.observation, WaterReading)
        and body.observation.reference_kind == "stage"
    ):
        station = db.get(Station, body.observation.reference_id)
        ref = station.payload.get("stage_reference", {}) if station else {}
        if (
            ref.get("approved") is not True
            or ref.get("revision") != body.observation.reference_revision
            or ref.get("unit") != "m"
        ):
            raise ApiError(
                422,
                "invalid_reference",
                "Stage reference is not approved at this revision",
            )
    if body.media_id:
        media = db.get(Media, body.media_id)
        if not media or media.owner_id != account.id:
            raise ApiError(404, "media_not_found", "Photo not found")
    r = CitizenReport(
        owner_id=account.id,
        idempotency_key=idempotency_key,
        payload_hash=digest,
        category=PREFIX + body.observation.kind,
        latitude=body.latitude,
        longitude=body.longitude,
        payload=payload,
        media_id=body.media_id,
    )
    db.add(r)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        r = (
            db.query(CitizenReport)
            .filter_by(owner_id=account.id, idempotency_key=idempotency_key)
            .first()
        )
        if not r or r.payload_hash != digest or not r.category.startswith(PREFIX):
            raise ApiError(
                409, "idempotency_conflict", "Submission could not be reconciled"
            )
    return project(db, r)


@router.get("/observations", response_model=Page[ObservationView])
def history(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    account=Depends(require_citizen),
    db: Session = Depends(get_db),
):
    q = query_v2(db).filter_by(owner_id=account.id)
    return {
        "items": [
            project(db, r)
            for r in q.order_by(CitizenReport.created_at.desc())
            .offset(offset)
            .limit(limit)
        ],
        "total": q.count(),
        "offset": offset,
        "limit": limit,
    }


@router.get("/observations/{rid}", response_model=ObservationView)
def detail(rid: str, account=Depends(require_account), db: Session = Depends(get_db)):
    r = query_v2(db).filter_by(id=rid).first()
    if not r or (
        r.owner_id != account.id and "report:review" not in account.capabilities
    ):
        raise ApiError(404, "report_not_found", "Observation not found")
    if r.owner_id != account.id:
        require_mfa(account)
    return project(db, r)


@router.get("/moderation/observations", response_model=Page[ObservationView])
def queue(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    account=Depends(require_reviewer),
    db: Session = Depends(get_db),
):
    q = query_v2(db).filter_by(status="pending")
    return {
        "items": [
            project(db, r)
            for r in q.order_by(CitizenReport.created_at).offset(offset).limit(limit)
        ],
        "total": q.count(),
        "offset": offset,
        "limit": limit,
    }


@router.post("/observations/{rid}/moderation", response_model=ObservationView)
def moderate(
    rid: str,
    body: ModerationInput,
    account=Depends(require_reviewer),
    db: Session = Depends(get_db),
):
    r = query_v2(db).filter_by(id=rid).with_for_update().first()
    if not r:
        raise ApiError(404, "report_not_found", "Observation not found")
    if r.status != "pending":
        raise ApiError(
            409, "already_reviewed", "This observation has already been reviewed"
        )
    r.status = body.status
    db.add(
        AuditEvent(
            actor_id=account.id,
            action="report.moderate",
            resource_id=r.id,
            details={"status": body.status, "reason": body.reason},
        )
    )
    db.commit()
    return project(db, r)


@router.get("/community/observations", response_model=Page[PublicObservation])
def community(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = query_v2(db).filter_by(status="approved")
    result = []
    # Public context is explicit. Free text, instrument/site identities and reference IDs stay private.
    fields = {
        "kind",
        "movement",
        "method",
        "response",
        "surfaces",
        "features",
        "amount_state",
        "value",
        "unit",
        "interval_start",
        "interval_end",
        "reference_kind",
        "subject",
        "calibration_status",
    }
    for r in q.order_by(CitizenReport.created_at.desc()).offset(offset).limit(limit):
        result.append(
            {
                "id": r.id,
                "protocol_id": PROTOCOL_ID,
                "protocol_revision": r.payload["protocol_revision"],
                "observation": {
                    k: v for k, v in r.payload["observation"].items() if k in fields
                },
                "latitude": round(r.latitude, 3),
                "longitude": round(r.longitude, 3),
                "location_precision": "rounded_0.001_degree",
                "observed_at": r.payload["observed_at"],
                "created_at": r.created_at,
            }
        )
    return {"items": result, "total": q.count(), "offset": offset, "limit": limit}


@router.get(
    "/observation-history", response_model=Page[ObservationView | LegacyObservationView]
)
def mixed_history(
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=500),
    account=Depends(require_citizen),
    db: Session = Depends(get_db),
):
    q = db.query(CitizenReport).filter_by(owner_id=account.id)
    rows = q.order_by(CitizenReport.created_at.desc()).offset(offset).limit(limit).all()
    result = []
    for r in rows:
        view = project(db, r)
        if not r.category.startswith(PREFIX):
            view = {**view, "protocol_id": "legacy-unspecified", "protocol_revision": 0}
        result.append(view)
    return {"items": result, "total": q.count(), "offset": offset, "limit": limit}
