"""Operational response is distinct from publication and scientific validation."""

from datetime import datetime, timezone, timedelta
from typing import Literal
from pydantic import Field, model_validator
from .observations import Strict, ObservationView
from ..http.contracts import ReportView


class EventInput(Strict):
    expected_revision: int = Field(ge=0)
    action: Literal[
        "acknowledge", "assign", "associate", "inspect", "act", "close", "reopen"
    ]
    reason: str = Field(min_length=3, max_length=1000)
    assignee_id: str | None = Field(default=None, min_length=1, max_length=36)
    plant_id: int | None = Field(default=None, ge=1)
    station_code: str | None = Field(default=None, min_length=1, max_length=120)
    result: Literal["confirmed", "not_confirmed", "unable_to_verify"] | None = None
    observed_at: datetime | None = None
    note: str | None = Field(default=None, min_length=3, max_length=2000)

    @model_validator(mode="after")
    def context(self):
        allowed = {
            "assign": {"assignee_id"},
            "associate": {"plant_id", "station_code"},
            "inspect": {"result", "observed_at", "note"},
            "act": {"note"},
            "close": {"note"},
        }.get(self.action, set())
        supplied = self.model_fields_set - {"expected_revision", "action", "reason"}
        if supplied - allowed:
            raise ValueError("Fields do not apply to this action")
        if self.action == "assign" and not self.assignee_id:
            raise ValueError("Select an eligible operator")
        if self.action == "associate" and not supplied:
            raise ValueError("Select or clear a plant/station")
        if self.action in {"inspect", "act", "close"} and not self.note:
            raise ValueError("Record method/evidence, action or disposition")
        if self.action == "inspect" and (not self.result or not self.observed_at):
            raise ValueError("Inspection needs result and observed time")
        if self.observed_at and (
            self.observed_at.tzinfo is None
            or self.observed_at > datetime.now(timezone.utc) + timedelta(minutes=5)
        ):
            raise ValueError("Inspection time needs timezone and cannot be future")
        return self


class ResponseState(Strict):
    revision: int
    state: Literal["unassigned", "assigned", "investigating", "closed"]
    assignee_id: str | None = None
    plant_id: int | None = None
    station_code: str | None = None
    updated_at: datetime | None = None


class ResponseEvent(Strict):
    id: str
    revision: int
    actor_id: str
    action: str
    reason: str
    details: dict
    created_at: datetime


class OperationsReport(Strict):
    report: ObservationView | ReportView
    response: ResponseState


class OperationsDetail(OperationsReport):
    events: list[ResponseEvent]


class Responder(Strict):
    id: str
    label: str


class RegistryItem(Strict):
    id: str
    label: str
