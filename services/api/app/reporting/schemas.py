from datetime import datetime, timezone, timedelta
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class ReportInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    category:Literal['rainfall','water_level','temperature','wastewater']
    reading_value:float|None=None
    reading_unit:str|None=None
    condition:Literal['normal','warning','critical']|None=None
    note:str|None=Field(None,max_length=2000)
    latitude:float=Field(ge=-90,le=90,allow_inf_nan=False)
    longitude:float=Field(ge=-180,le=180,allow_inf_nan=False)
    location_accuracy_m:float|None=Field(None,ge=0,allow_inf_nan=False)
    station_code:str|None=Field(None,max_length=80)
    media_id:str|None=None
    observed_at:datetime

    @model_validator(mode='after')
    def correct_semantics(self):
        if self.observed_at.tzinfo is None:raise ValueError('Observation time requires a timezone')
        if self.observed_at > datetime.now(timezone.utc)+timedelta(minutes=5):raise ValueError('Observation time is in the future')
        if self.category=='wastewater':
            if not self.condition or self.reading_value is not None or self.reading_unit is not None:
                raise ValueError('Wastewater requires a condition, not a numeric reading')
        else:
            import math
            units={'rainfall':'mm','water_level':'m','temperature':'°C'}
            if self.reading_value is None or not math.isfinite(self.reading_value) or self.reading_unit!=units[self.category] or self.condition:
                raise ValueError('Reading category/value/unit do not agree')
            if self.category!='temperature' and self.reading_value<0:raise ValueError('Reading must be nonnegative')
        return self

class ModerationInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    status:Literal['approved','rejected']
    reason:str=Field(min_length=1,max_length=2000)
