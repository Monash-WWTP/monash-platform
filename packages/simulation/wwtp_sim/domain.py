"""Domain types shared by all simulation models."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Literal

Horizon = Literal["1_month", "3_months", "6_months"]

HORIZON_DAYS: dict[str, int] = {
    "1_month": 30,
    "3_months": 90,
    "6_months": 180,
}

EFFLUENT_METRICS = [
    "bod",
    "cod",
    "tss",
    "ammonia",
    "nitrate",
    "phosphorus",
    "turbidity",
    "ph",
]

DemandLevel = Literal["low", "normal", "high"]
WeatherLevel = Literal["dry", "normal", "wet"]
UnitType = Literal["pump", "aeration", "clarifier"]


@dataclass
class InfluentConditions:
    """Baseline influent assumptions. Units: flow MLD, concentrations mg/L."""

    flow: float = 40.0
    bod: float = 220.0  # BOD5; used as the influent load in guideline Eq. 5.25.
    cod: float = 480.0
    tss: float = 240.0
    ammonia: float = 35.0
    # Equation 5.28 requires influent Kjeldahl nitrogen (TKN), not ammonia.
    # The default is the documented baseline assumption when no measurement is
    # supplied; older scenario payloads therefore remain compatible.
    tkn: float = 40.0


@dataclass
class Forecast:
    demand: DemandLevel = "normal"
    demand_multiplier: float | None = None  # custom override, e.g. 1.25
    demand_change_pct: float | None = None  # numeric override, e.g. 25.0
    weather: WeatherLevel = "normal"
    rainfall_mm_day: float | None = None  # numeric override for new scenarios
    influent: InfluentConditions = field(default_factory=InfluentConditions)


@dataclass
class MaintenanceEvent:
    unit_type: UnitType
    start_date: date
    duration_days: int
    availability_pct: float = 50.0  # availability of the unit during the event

    def active_on(self, day: date) -> bool:
        return self.start_date <= day < self.start_date + timedelta(days=self.duration_days)


@dataclass
class OperatingParameters:
    capacity_mld: float = 60.0
    aeration_availability: float = 100.0
    pump_availability: float = 100.0
    clarifier_availability: float = 100.0
    # Guideline recovery/removal terms in Equations 5.25 and 5.28.
    ch4_recovered_kg_m3: float = 0.0
    n2o_recovered_kg_m3: float = 0.0


@dataclass
class EmissionFactors:
    """GHG emission factors (Tables 5.6 / 5.8). Defaults: integrated general EF."""

    ef_ch4: float = 0.0121  # kg CH4 / kg BOD5
    ef_n2o: float = 0.0093  # kg N2O-N / kg N


@dataclass
class SimulationInput:
    forecast: Forecast
    maintenance: list[MaintenanceEvent]
    operating_parameters: OperatingParameters
    horizon: Horizon
    start_date: date
    compliance_limits: dict[str, float] = field(default_factory=dict)
    emission_factors: EmissionFactors = field(default_factory=EmissionFactors)
    seed: int = 42


@dataclass
class Exceedance:
    """A contiguous period where a predicted metric exceeds its discharge limit."""

    metric: str
    start_day: int
    end_day: int
    peak_value: float
    limit_value: float
    peak_ratio: float  # peak_value / limit_value
    factors: list[str]  # observable contributing conditions during the period


@dataclass
class SimulationResult:
    """Daily predicted effluent series, GHG intensities, KPIs and exceedances."""

    dates: list[date]
    predicted_effluent: dict[str, list[float]]  # metric -> daily values
    influent_flow: list[float]
    capacity_utilization: list[float]
    unit_availability: dict[str, list[float]]  # unit_type -> daily availability %
    ghg: dict[str, list[float]]  # 'ch4' / 'n2o' -> daily kg CO2-eq/m3
    kpis: dict[str, float | str]
    exceedances: list[Exceedance]
    model_id: str = ""
    model_version: str = ""
