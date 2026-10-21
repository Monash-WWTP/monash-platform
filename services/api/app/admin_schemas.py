"""Bounded administration inputs; scientific provenance is supplied, never certified."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictInput(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False, str_strip_whitespace=True)


class RoleChange(StrictInput):
    capabilities: list[Literal['report:own','report:respond','report:review','monitor:read','scenario:operate']]
    expected_capabilities: list[str]
    reason: str = Field(min_length=3,max_length=1000)


class Equipment(StrictInput):
    unit_type: Literal['pump','aeration','clarifier']
    name: str = Field(min_length=1,max_length=200)
    baseline_availability: float = Field(ge=0,le=100)


CANONICAL_UNITS = {**dict.fromkeys(('bod','cod','tss','ammonia','nitrate','phosphorus'),'mg/L'),
    'turbidity':'NTU'}


class Threshold(StrictInput):
    metric: str
    value: float = Field(gt=0)
    unit: str
    source: str = Field(min_length=3,max_length=2000)
    applicability: str = Field(min_length=3,max_length=2000)

    @model_validator(mode='after')
    def supported(self):
        if self.metric not in CANONICAL_UNITS or self.unit != CANONICAL_UNITS[self.metric]:
            raise ValueError('Use a supported metric and its canonical unit')
        return self


class Factors(StrictInput):
    ef_ch4: float = Field(ge=0)
    ef_n2o: float = Field(ge=0)
    ch4_unit: Literal['kg CH4/kg BOD5']
    n2o_unit: Literal['kg N2O-N/kg N']
    source: str = Field(min_length=3,max_length=2000)
    applicability: str = Field(min_length=3,max_length=2000)


class Configuration(StrictInput):
    thresholds: list[Threshold] = Field(max_length=8)
    emission_factors: Factors

    @model_validator(mode='after')
    def unique_metrics(self):
        if len({t.metric for t in self.thresholds}) != len(self.thresholds):
            raise ValueError('Each threshold metric may appear only once')
        return self


class PlantWrite(StrictInput):
    code: str = Field(min_length=1,max_length=100,pattern=r'^[A-Za-z0-9_-]+$')
    name: str = Field(min_length=1,max_length=200)
    latitude: float = Field(ge=-90,le=90)
    longitude: float = Field(ge=-180,le=180)
    capacity_mld: float = Field(gt=0)
    description: str = Field(default='',max_length=4000)
    stp_type: str = Field(default='',max_length=100)
    status: Literal['unknown','operational','maintenance'] = 'unknown'
    units: list[Equipment] = Field(default_factory=list,max_length=100)
    configuration: Configuration
    reason: str = Field(min_length=3,max_length=1000)
    expected_revision: int = Field(default=0,ge=0)


class StationWrite(StrictInput):
    code: str = Field(min_length=1,max_length=100,pattern=r'^[A-Za-z0-9_-]+$')
    name: str = Field(min_length=1,max_length=200)
    category: Literal['A','B'] | None = None
    stp_type: str | None = Field(default=None,max_length=100)
    latitude: float = Field(ge=-90,le=90)
    longitude: float = Field(ge=-180,le=180)
    reason: str = Field(min_length=3,max_length=1000)
    expected_revision: str | None = None


# Explicit response projections keep subjects, credentials and session material
# outside the administration API contract.
from datetime import datetime
from pydantic import JsonValue


class StrictOutput(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class AdminAccountView(StrictOutput):
    id: str
    email: str
    capabilities: list[str]
    created_at: datetime


class ThresholdView(StrictOutput):
    metric: str
    value: float
    unit: str
    source: str
    applicability: str


class FactorView(StrictOutput):
    ef_ch4: float
    ef_n2o: float
    ch4_unit: Literal['kg CH4/kg BOD5']
    n2o_unit: Literal['kg N2O-N/kg N']
    source: str
    applicability: str


class ConfigurationView(StrictOutput):
    thresholds: list[ThresholdView]
    emission_factors: FactorView


class EquipmentView(StrictOutput):
    unit_type: str
    name: str
    baseline_availability: float


class AdminPlantView(StrictOutput):
    id: int
    code: str | None
    name: str
    latitude: float
    longitude: float
    capacity_mld: float
    description: str
    stp_type: str
    status: str
    revision: int
    units: list[EquipmentView]
    configuration: ConfigurationView
    provenance_status: Literal['supplied_unverified','legacy_unknown']


class AdminStationPayload(BaseModel):
    # Imported historical metadata remains visible to authorized administrators.
    model_config = ConfigDict(extra='allow', allow_inf_nan=False)
    code: str
    name: str
    category: str | None
    stp_type: str | None
    latitude: float
    longitude: float
    created_at: datetime


class AdminStationView(StrictOutput):
    code: str
    payload: AdminStationPayload
    revision: str


class AdminHistoryDetails(StrictOutput):
    reason: str
    before: JsonValue = None
    after: JsonValue = None


class AdminHistoryEvent(StrictOutput):
    id: str
    actor_id: str | None
    action: Literal['admin.account.capabilities','admin.plant.configuration','admin.station.metadata','account.capabilities']
    resource_id: str
    created_at: datetime
    details: AdminHistoryDetails


class AdminDependencies(StrictOutput):
    database: Literal['ready','unavailable']
    storage: Literal['ready','unavailable']
    identity: Literal['ready','unavailable']


class AdminModelStatus(StrictOutput):
    id: str
    version: str
    validation_status: Literal['illustrative_unvalidated']
    decision_use_permitted: Literal[False]


class AdminStatus(StrictOutput):
    environment: str
    dependencies: AdminDependencies
    model: AdminModelStatus
    release_acceptance: Literal['pending_external_acceptance']
