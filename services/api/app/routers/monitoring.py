"""Monitoring reads retain laboratory provenance; community data has its own contract."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..db.platform import Station, Sample
from ..http.contracts import Page, StationView, SampleView

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/stations", response_model=Page[StationView])
def stations(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(Station)
    return {
        "items": [
            r.payload for r in query.order_by(Station.code).offset(offset).limit(limit)
        ],
        "total": query.count(),
        "offset": offset,
        "limit": limit,
    }


@router.get("/samples", response_model=Page[SampleView])
def samples(
    station_code: str,
    year: int | None = None,
    compliance: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(Sample).filter_by(station_code=station_code)
    if year is not None:
        query = query.filter(Sample.payload["source_year"].as_integer() == year)
    if compliance is not None:
        query = query.filter(Sample.payload["compliance"].as_string() == compliance)
    return {
        "items": [
            r.payload for r in query.order_by(Sample.id).offset(offset).limit(limit)
        ],
        "total": query.count(),
        "offset": offset,
        "limit": limit,
    }


@router.get("/years", response_model=list[int])
def years(station_code: str, db: Session = Depends(get_db)):
    return sorted(
        {
            r.payload["source_year"]
            for r in db.query(Sample).filter_by(station_code=station_code)
        }
    )
