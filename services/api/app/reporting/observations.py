"""Versioned citizen protocol. Publication approval never certifies a measurement."""
from datetime import datetime, timezone, timedelta
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

PROTOCOL_ID = 'citizen-observation'
REVISION = 1
LEGACY_CATEGORIES = ('rainfall', 'water_level', 'temperature', 'wastewater')

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class Presence(Strict):
    kind: Literal['flooding', 'rain_occurrence']
    method: Literal['visual']
    response: Literal['present', 'not_observed', 'unknown']
    surfaces: list[Literal['road', 'path', 'property', 'other']] = Field(default_factory=list, max_length=4)
    @model_validator(mode='after')
    def coherent(self):
        if len(set(self.surfaces)) != len(self.surfaces): raise ValueError('Duplicate surfaces')
        if self.kind == 'rain_occurrence' and self.surfaces: raise ValueError('Rain does not use surface classes')
        if self.response != 'present' and self.surfaces: raise ValueError('Surface classes require observed flooding')
        if self.kind == 'flooding' and self.response == 'present' and not self.surfaces: raise ValueError('Identify the affected surface')
        return self

class Appearance(Strict):
    kind: Literal['water_appearance']
    method: Literal['visual']
    response: Literal['features_observed', 'not_observed', 'unknown']
    features: list[Literal['discoloration','foam','debris','sheen','overflow','other']] = Field(default_factory=list, max_length=6)
    @model_validator(mode='after')
    def coherent(self):
        if len(set(self.features)) != len(self.features): raise ValueError('Duplicate features')
        if (self.response == 'features_observed') != bool(self.features): raise ValueError('Features and response disagree')
        return self

class Rainfall(Strict):
    kind: Literal['rainfall_accumulation']
    method: Literal['instrument']
    amount_state: Literal['value','trace','missing']
    value: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    unit: Literal['mm']
    interval_start: datetime
    interval_end: datetime
    gauge_type: str = Field(min_length=1, max_length=120)
    gauge_id: str = Field(min_length=1, max_length=120)
    @model_validator(mode='after')
    def interval(self):
        if self.interval_start.tzinfo is None or self.interval_end.tzinfo is None: raise ValueError('Rain interval needs timezone')
        if self.interval_start >= self.interval_end: raise ValueError('Rain interval must have positive duration')
        if (self.amount_state == 'value') != (self.value is not None): raise ValueError('Trace/missing are not numeric zero')
        return self

class WaterReading(Strict):
    kind: Literal['water_reading']
    method: Literal['instrument','estimate']
    value: float = Field(allow_inf_nan=False)
    unit: Literal['m']
    reference_kind: Literal['depth','stage']
    reference_description: str | None = Field(default=None, min_length=1, max_length=160)
    reference_id: str | None = Field(default=None, min_length=1, max_length=80)
    reference_revision: int | None = Field(default=None, ge=1)
    instrument: str | None = Field(default=None, min_length=1, max_length=120)
    @model_validator(mode='after')
    def reference(self):
        if self.reference_kind == 'depth':
            if self.value < 0 or not self.reference_description or self.reference_id or self.reference_revision: raise ValueError('Depth needs nonnegative value and surface reference')
        elif not self.reference_id or not self.reference_revision or self.reference_description or self.method != 'instrument':
            raise ValueError('Stage requires instrument and registered reference revision')
        if self.method == 'instrument' and not self.instrument: raise ValueError('Identify the measurement instrument')
        return self

class Temperature(Strict):
    kind: Literal['temperature']
    method: Literal['instrument']
    value: float = Field(ge=-273.15, allow_inf_nan=False)
    unit: Literal['°C']
    subject: Literal['air','water']
    instrument: str = Field(min_length=1, max_length=120)
    sample_context: str = Field(min_length=1, max_length=160)
    calibration_status: Literal['known','unknown']
    calibration_note: str | None = Field(default=None, min_length=1, max_length=200)
    @model_validator(mode='after')
    def calibration(self):
        if self.calibration_status == 'known' and not self.calibration_note: raise ValueError('Describe known calibration provenance')
        return self

Observation = Annotated[Presence | Appearance | Rainfall | WaterReading | Temperature, Field(discriminator='kind')]

class ObservationInput(Strict):
    protocol_id: Literal['citizen-observation']
    protocol_revision: Literal[1]
    observation: Observation
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    location_source: Literal['current','selected']
    location_accuracy_m: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    observed_at: datetime
    note: str | None = Field(default=None, max_length=2000)
    media_id: str | None = None
    @model_validator(mode='after')
    def time(self):
        if self.observed_at.tzinfo is None or self.observed_at > datetime.now(timezone.utc)+timedelta(minutes=5): raise ValueError('Observation time needs timezone and cannot be in the future')
        if isinstance(self.observation,Rainfall) and self.observation.interval_end > self.observed_at: raise ValueError('Rain interval cannot end after observation')
        return self

class ObservationView(ObservationInput):
    id: str
    moderation_status: Literal['pending','approved','rejected']
    review_reason: str | None = None
    created_at: datetime

class PublicObservation(Strict):
    id: str
    protocol_id: Literal['citizen-observation']
    protocol_revision: Literal[1]
    observation: dict
    latitude: float
    longitude: float
    location_precision: Literal['rounded_0.001_degree']
    observed_at: datetime
    created_at: datetime
