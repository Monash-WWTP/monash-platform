from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

Horizon = Literal["1_month", "3_months", "6_months"]


# ---------- forecast / maintenance payloads ----------

class InfluentIn(BaseModel):
    flow: float = 40.0
    bod: float = 220.0
    cod: float = 480.0
    tss: float = 240.0
    ammonia: float = 35.0
    # Influent Kjeldahl nitrogen required by carbon-accounting Eq. 5.28.
    # Defaults server-side so the existing frontend payload remains valid.
    tkn: float = Field(default=40.0, ge=0)


class ForecastIn(BaseModel):
    demand: Literal["low", "normal", "high"] = "normal"
    demand_multiplier: float | None = None
    demand_change_pct: float | None = Field(default=None, ge=-100, le=100)
    weather: Literal["dry", "normal", "wet"] = "normal"
    rainfall_mm_day: float | None = Field(default=None, ge=0, le=200)
    influent: InfluentIn = Field(default_factory=InfluentIn)


class MaintenanceEventIn(BaseModel):
    unit_type: Literal["pump", "aeration", "clarifier"]
    start_date: date
    duration_days: int = Field(ge=1, le=180)
    availability_pct: float = Field(default=50.0, ge=0, le=100)


class OperatingParametersIn(BaseModel):
    capacity_mld: float | None = None  # default: plant capacity
    aeration_availability: float = Field(default=100.0, ge=0, le=100)
    pump_availability: float = Field(default=100.0, ge=0, le=100)
    clarifier_availability: float = Field(default=100.0, ge=0, le=100)
    ch4_recovered_kg_m3: float = Field(default=0.0, ge=0)
    n2o_recovered_kg_m3: float = Field(default=0.0, ge=0)


# ---------- plants ----------

class PlantUnitOut(BaseModel):
    id: int
    unit_type: str
    name: str
    baseline_availability: float

    model_config = {"from_attributes": True}


class ComplianceLimitOut(BaseModel):
    metric: str
    limit_value: float
    unit: str

    model_config = {"from_attributes": True}


class PlantOut(BaseModel):
    id: int
    code: str | None = None
    name: str
    status: str
    latitude: float
    longitude: float
    capacity_mld: float
    description: str

    model_config = {"from_attributes": True}


class PlantDetailOut(PlantOut):
    units: list[PlantUnitOut] = []
    compliance_limits: list[ComplianceLimitOut] = []


# ---------- scenarios ----------

class ScenarioIn(BaseModel):
    name: str
    horizon: Horizon = "3_months"
    forecast: ForecastIn = Field(default_factory=ForecastIn)
    maintenance: list[MaintenanceEventIn] = []
    operating_parameters: OperatingParametersIn = Field(default_factory=OperatingParametersIn)
    is_baseline: bool = False

    model_config = {"json_schema_extra": {"examples": [{
        "name": "Synthetic aeration maintenance",
        "horizon": "3_months",
        "forecast": {"demand": "normal", "weather": "normal"},
        "maintenance": [{"unit_type": "aeration", "start_date": "2026-01-01",
                         "duration_days": 7, "availability_pct": 50}],
        "operating_parameters": {"capacity_mld": 10},
        "is_baseline": False,
    }]}}


class ScenarioOut(BaseModel):
    id: int
    plant_id: int
    name: str
    horizon: str
    forecast: dict
    maintenance: list
    operating_parameters: dict
    is_baseline: bool
    created_at: datetime
    latest_run_id: int | None = None

    model_config = {"from_attributes": True}


# ---------- runs ----------

class RunRequest(BaseModel):
    model_id: str = "effluent_v1"


class ExceedanceOut(BaseModel):
    metric: str
    start_day: int
    end_day: int
    peak_value: float
    limit_value: float
    peak_ratio: float
    factors: list[str]


class RunOut(BaseModel):
    id: int
    scenario_id: int
    scenario_name: str
    plant_id: int
    horizon: str
    model_id: str
    model_version: str
    validation_status: Literal["illustrative_unvalidated"] = "illustrative_unvalidated"
    decision_use_permitted: Literal[False] = False
    status: str
    kpis: dict
    exceedances: list[ExceedanceOut]
    created_at: datetime

    model_config = {"json_schema_extra": {"examples": [{
        "id": 1, "scenario_id": 1, "scenario_name": "Synthetic baseline",
        "plant_id": 1, "horizon": "3_months", "model_id": "effluent_v1",
        "model_version": "1.4.0", "validation_status": "illustrative_unvalidated",
        "decision_use_permitted": False, "status": "completed",
        "kpis": {"compliance_pct": 100.0}, "exceedances": [],
        "created_at": "2026-01-01T00:00:00",
    }]}}


class TimeseriesOut(BaseModel):
    run_id: int
    dates: list[str]
    series: dict[str, list[float]]
    compliance_limits: dict[str, float]


class CompareRequest(BaseModel):
    run_ids: list[int] = Field(min_length=2, max_length=4)


class CompareOut(BaseModel):
    runs: list[RunOut]
    timeseries: list[TimeseriesOut]


class ModelOut(BaseModel):
    model_id: str
    name: str
    version: str
    description: str
