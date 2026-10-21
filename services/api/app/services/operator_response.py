"""Serialize writes through the original report; state, event and audit share a transaction."""

from sqlalchemy import or_
from ..db.platform import (
    CitizenReport,
    ReportResponse,
    ReportResponseEvent,
    Account,
    Station,
    AuditEvent,
    now,
)
from ..db.models import Plant
from ..http.errors import ApiError
from ..routers.observations import project

STATES = {"unassigned", "assigned", "investigating", "closed"}


def state_view(state):
    if not state:
        return {"revision": 0, "state": "unassigned"}
    return {
        k: getattr(state, k)
        for k in (
            "revision",
            "state",
            "assignee_id",
            "plant_id",
            "station_code",
            "updated_at",
        )
    }


def item(db, report):
    return {
        "report": project(db, report),
        "response": state_view(db.get(ReportResponse, report.id)),
    }


def detail(db, rid):
    report = db.get(CitizenReport, rid)
    if not report:
        raise ApiError(404, "report_not_found", "Report not found")
    events = (
        db.query(ReportResponseEvent)
        .filter_by(report_id=rid)
        .order_by(ReportResponseEvent.revision)
        .all()
    )
    return {
        **item(db, report),
        "events": [
            {
                k: getattr(e, k)
                for k in (
                    "id",
                    "revision",
                    "actor_id",
                    "action",
                    "reason",
                    "details",
                    "created_at",
                )
            }
            for e in events
        ],
    }


def listing(db, state, offset, limit):
    q = db.query(CitizenReport).outerjoin(
        ReportResponse, ReportResponse.report_id == CitizenReport.id
    )
    if state == "unassigned":
        q = q.filter(
            or_(
                ReportResponse.state == "unassigned", ReportResponse.report_id.is_(None)
            )
        )
    elif state:
        q = q.filter(ReportResponse.state == state)
    return {
        "items": [
            item(db, r)
            for r in q.order_by(CitizenReport.created_at.desc(), CitizenReport.id)
            .offset(offset)
            .limit(limit)
        ],
        "total": q.count(),
        "offset": offset,
        "limit": limit,
    }


def eligible(db, account_id):
    account = db.get(Account, account_id)
    return account and "report:respond" in account.capabilities


def mutate(db, actor, rid, body):
    report = db.query(CitizenReport).filter_by(id=rid).with_for_update().first()
    if not report:
        raise ApiError(404, "report_not_found", "Report not found")
    current = db.get(ReportResponse, rid)
    revision = current.revision if current else 0
    state = current.state if current else "unassigned"
    if body.expected_revision != revision:
        raise ApiError(
            409,
            "stale_response",
            "Response changed. Reload and review before retrying.",
        )
    if (
        state == "closed"
        and body.action != "reopen"
        or body.action == "reopen"
        and state != "closed"
    ):
        raise ApiError(
            409,
            "invalid_transition",
            "Reopen a closed case before recording further actions",
        )
    if body.action == "assign" and not eligible(db, body.assignee_id):
        raise ApiError(
            422, "invalid_assignee", "Select an eligible responding operator"
        )
    if body.action == "associate":
        if (
            body.plant_id is not None
            and not db.get(Plant, body.plant_id)
            or body.station_code is not None
            and not db.get(Station, body.station_code)
        ):
            raise ApiError(
                422, "invalid_association", "Select an existing plant or station"
            )
    if (
        body.action == "close"
        and not db.query(ReportResponseEvent)
        .filter(
            ReportResponseEvent.report_id == rid,
            ReportResponseEvent.action.in_(["inspect", "act"]),
        )
        .first()
    ):
        raise ApiError(
            422, "missing_disposition", "Record an inspection or action before closing"
        )
    if not current:
        current = ReportResponse(report_id=rid, revision=0, state="unassigned")
        db.add(current)
    if body.action in {"acknowledge", "inspect", "reopen"}:
        current.state = "investigating"
    if body.action == "assign":
        current.assignee_id = body.assignee_id
        if current.state != "investigating":
            current.state = "assigned"
    if body.action == "associate":
        if "plant_id" in body.model_fields_set:
            current.plant_id = body.plant_id
        if "station_code" in body.model_fields_set:
            current.station_code = body.station_code
    if body.action == "close":
        current.state = "closed"
    current.revision = revision + 1
    current.updated_at = now()
    details = body.model_dump(
        mode="json",
        exclude={"expected_revision", "action", "reason"},
        exclude_unset=True,
    )
    db.add(
        ReportResponseEvent(
            report_id=rid,
            revision=current.revision,
            actor_id=actor.id,
            action=body.action,
            reason=body.reason,
            details=details,
        )
    )
    db.add(
        AuditEvent(
            actor_id=actor.id,
            action="report.response." + body.action,
            resource_id=rid,
            details={
                "revision": current.revision,
                "reason": body.reason,
                "state": current.state,
            },
        )
    )
    db.commit()
    return detail(db, rid)
