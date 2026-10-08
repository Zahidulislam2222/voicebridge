"""Validated domain inputs. Caller data never supplies a tenant or credential."""

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .protocol import SINGLE_EMAIL_PATTERN


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, hide_input_in_errors=True)


class CallIntentInput(Input):
    provider: Literal["retell", "vapi"]


class CallIntentBinding(Input):
    intent_id: str = Field(min_length=1, max_length=100)
    external_id: str = Field(min_length=1, max_length=100)


class BookingInput(Input):
    operation_id: str = Field(min_length=1, max_length=100, pattern=r"^[\w-]+$")
    name: str = Field(min_length=1, max_length=200)
    phone: str = Field(min_length=7, max_length=25)
    email: str = Field(min_length=3, max_length=254)
    service: str = Field(min_length=1, max_length=100)
    start: datetime
    confirmed: bool
    call_id: str | None = Field(default=None, max_length=100)

    @field_validator("email")
    @classmethod
    def email_valid(cls, value: str) -> str:
        if not re.fullmatch(SINGLE_EMAIL_PATTERN, value):
            raise ValueError("Invalid email")
        return value.lower()

    @field_validator("phone")
    @classmethod
    def phone_valid(cls, value: str) -> str:
        if not re.fullmatch(r"[+\d ()-]+", value) or not 7 <= len(re.sub(r"\D", "", value)) <= 15:
            raise ValueError("Invalid phone")
        return value

    @field_validator("name")
    @classmethod
    def plain_name(cls, value: str) -> str:
        if any(ord(c) < 32 for c in value):
            raise ValueError("Invalid name")
        return value


class ChangeInput(Input):
    operation_id: str = Field(min_length=1, max_length=100, pattern=r"^[\w-]+$")
    action: Literal["cancel", "reschedule"]
    start: datetime | None = None
    confirmed: bool
    expected_revision: int = Field(ge=1)


class DocumentInput(Input):
    name: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1)
    expected_revision: int | None = None
    fact_key: str | None = Field(default=None, max_length=100)


class AgentInput(Input):
    name: str = Field(min_length=1, max_length=200)
    greeting: str = Field(min_length=1, max_length=1000)
    handoff: str = Field(min_length=1, max_length=1000)
    voice_id: str = Field(min_length=1, max_length=100)
    expected_revision: int = Field(ge=1)


class ToolInput(Input):
    name: str
    arguments: dict[str, Any]


class QuestionInput(Input):
    query: str = Field(strict=True, min_length=1)


class AvailabilityInput(Input):
    start: datetime
    service: str = Field(strict=True, min_length=1)


class BookingLookupInput(Input):
    booking_id: str = Field(strict=True, min_length=1, max_length=100, pattern=r"^[\w-]+$")


class Output(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class AppointmentView(Output):
    id: str
    contact_id: str
    call_id: str | None
    service: str
    start: datetime
    end: datetime
    status: str
    external_id: str | None
    revision: int


class ContactView(Output):
    id: str
    name: str
    email: str
    phone: str
    notes: str


class JobView(Output):
    id: str
    kind: str
    status: str
    attempts: int
    detail: str
    booking_id: str | None
    receipt: str | None


class TranscriptEntry(Output):
    speaker: str
    text: str


class CallView(Output):
    id: str
    provider: str
    state: str
    date: datetime
    transcript: list[TranscriptEntry]


class DocumentView(Output):
    id: str
    name: str
    text: str
    revision: int
    updated: datetime
    checksum: str


class AuditView(Output):
    id: str
    action: str
    target: str
    date: datetime


class AgentView(Output):
    name: str
    greeting: str
    handoff: str
    voice_id: str
    revision: int


class StateView(Output):
    appointments: list[AppointmentView]
    contacts: list[ContactView]
    jobs: list[JobView]
    calls: list[CallView]
    documents: list[DocumentView]
    audit: list[AuditView]
    agent: AgentView | None
    record_limit: int
    counts: dict[str, int]
    integrations: dict[str, str]
    evaluation_fixtures: list["EvaluationFixtureView"]
    synthetic: bool


class EvaluationFixtureView(Output):
    id: str
    status: str
    booking_ids: list[str]
    detail: str


class DomainError(Exception):
    def __init__(self, code: str, status: int = 409) -> None:
        self.code = code
        self.status = status
        super().__init__(code)
