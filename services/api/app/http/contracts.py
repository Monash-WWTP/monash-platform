"""Documented response contracts; unknown private fields cannot cross projections."""

from datetime import datetime, date
from typing import Generic, TypeVar, Literal
from pydantic import BaseModel, ConfigDict
from ..reporting.schemas import ReportInput

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    offset: int
    limit: int


class AccountView(BaseModel):
    id: str
    email: str
    capabilities: list[str]


class StationView(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str
    name: str
    stp_type: str | None
    category: str | None
    latitude: float
    longitude: float
    created_at: datetime


class SampleView(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int
    station_code: str
    sample_date: date
    sampling: int
    sample_point: str
    bod: float | None
    bod_bdl: bool
    cod: float | None
    cod_bdl: bool
    nh3n: float | None
    nh3n_bdl: bool
    no3n: float | None
    no3n_bdl: bool
    ph: float | None
    ph_bdl: bool
    oil_grease: float | None
    oil_grease_bdl: bool
    tss: float | None
    tss_bdl: bool
    temperature: float | None
    compliance: str
    source_year: int
    created_at: datetime


class ReportView(ReportInput):
    id: str
    moderation_status: Literal["pending", "approved", "rejected"]
    created_at: datetime


class MediaView(BaseModel):
    id: str
    sha256: str
    byte_size: int
    mime: str


class CommunityView(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    category: Literal["rainfall", "water_level", "temperature", "wastewater"]
    condition: Literal["normal", "warning", "critical"] | None
    reading_value: float | None
    reading_unit: str | None
    latitude: float
    longitude: float
    location_precision: Literal["rounded_0.001_degree"]
    observed_at: datetime
    created_at: datetime
