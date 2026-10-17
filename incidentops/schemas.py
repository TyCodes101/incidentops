"""Validated API request and response contracts."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Status(str, Enum):
    open = "open"
    investigating = "investigating"
    resolved = "resolved"


class IncidentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(default="", max_length=3000)
    severity: Severity
    category: str = Field(default="other", min_length=2, max_length=40)


class IncidentUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    status: Status | None = None
    severity: Severity | None = None
    title: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=3000)
    category: str | None = Field(default=None, min_length=2, max_length=40)
    assignee_id: int | None = Field(default=None, ge=1)


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    severity: Severity
    status: Status
    category: str
    assignee_id: int | None
    created_at: datetime
    updated_at: datetime


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    action: str
    detail: str
    occurred_at: datetime
    actor: str


class MetricsRead(BaseModel):
    total: int
    unresolved: int
    by_severity: dict[str, int]
    by_status: dict[str, int]
