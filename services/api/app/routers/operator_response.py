from typing import Literal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..db.platform import Account, Station
from ..db.models import Plant
from ..identity.dependencies import require_responder
from ..http.contracts import Page
from ..reporting.operator_response import (
    EventInput,
    OperationsReport,
    OperationsDetail,
    Responder,
    RegistryItem,
)
from ..services import operator_response as service

router = APIRouter(prefix="/operations", tags=["operator response"])


@router.get("/reports", response_model=Page[OperationsReport])
def reports(
    state: Literal["unassigned", "assigned", "investigating", "closed"] | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    actor=Depends(require_responder),
):
    return service.listing(db, state, offset, limit)


@router.get("/responders", response_model=list[Responder])
def responders(db: Session = Depends(get_db), actor=Depends(require_responder)):
    return [
        {"id": a.id, "label": a.email}
        for a in db.query(Account).order_by(Account.email, Account.id)
        if "report:respond" in a.capabilities
    ]


@router.get("/plants", response_model=list[RegistryItem])
def plants(db: Session = Depends(get_db), actor=Depends(require_responder)):
    return [
        {"id": str(p.id), "label": p.name} for p in db.query(Plant).order_by(Plant.id)
    ]


@router.get("/stations", response_model=list[RegistryItem])
def stations(db: Session = Depends(get_db), actor=Depends(require_responder)):
    return [
        {"id": s.code, "label": str(s.payload.get("name", s.code))}
        for s in db.query(Station).order_by(Station.code)
    ]


@router.get("/reports/{rid}", response_model=OperationsDetail)
def detail(rid: str, db: Session = Depends(get_db), actor=Depends(require_responder)):
    return service.detail(db, rid)


@router.post("/reports/{rid}/events", response_model=OperationsDetail)
def event(
    rid: str,
    body: EventInput,
    db: Session = Depends(get_db),
    actor=Depends(require_responder),
):
    return service.mutate(db, actor, rid, body)
