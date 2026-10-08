"""Tenant-scoped business transactions shared by HTTP, voice tools and MCP."""

import hashlib
import json
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import DateTime, and_, cast, func, or_, select
from sqlalchemy.orm import Session, sessionmaker

from .connectors import Calendar
from .contracts import AgentInput, BookingInput, ChangeInput, DocumentInput, DomainError
from .db import (
    Appointment,
    Audit,
    Call,
    Contact,
    Document,
    Job,
    Operation,
    Record,
    Tenant,
    now,
    tenant_lock,
)
from .settings import Business, EvaluationSuite, ProviderProfiles, Settings, read_data


def identity() -> str:
    return uuid.uuid4().hex


def fingerprint(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def audit(session: Session, tenant: str, action: str, target: str) -> None:
    session.add(Audit(id=identity(), tenant_id=tenant, action=action, target=target))


def booking_view(row: Appointment) -> dict[str, Any]:
    return {
        "id": row.id,
        "contact_id": row.contact_id,
        "call_id": row.call_id,
        "service": row.service,
        "start": row.start.isoformat(),
        "end": row.end.isoformat(),
        "status": row.status,
        "external_id": row.external_id,
        "revision": row.revision,
    }


class Service:
    def __init__(
        self, settings: Settings, sessions: sessionmaker[Session], calendar: Calendar
    ) -> None:
        self.settings, self.sessions, self.calendar = settings, sessions, calendar
        self.business = Business.model_validate(read_data(settings.data_file))
        self.evaluations = EvaluationSuite.model_validate(read_data(settings.evaluation_file))
        self.profiles = ProviderProfiles.model_validate(read_data(settings.profile_file))

    def seed(self, tenant: str) -> None:
        if len(self.business.knowledge) > self.settings.max_documents:
            raise DomainError("document_limit", 422)
        documents = [DocumentInput.model_validate(item) for item in self.business.knowledge]
        for value in documents:
            self.validate_document(value)
        with self.sessions.begin() as s:
            tenant_lock(s, tenant)
            if s.get(Tenant, tenant):
                return
            s.add(Tenant(id=tenant, name=self.business.name))
            s.flush()
            s.add(
                Record(
                    id=identity(),
                    tenant_id=tenant,
                    kind="agent",
                    key="draft",
                    value={
                        "name": self.business.name,
                        "greeting": self.business.greeting,
                        "handoff": self.business.handoff,
                        "voice_id": self.business.voice_id,
                    },
                )
            )
            for item in documents:
                s.add(
                    Document(
                        id=identity(),
                        tenant_id=tenant,
                        name=item.name,
                        text=item.text,
                        checksum=hashlib.sha256(item.text.encode()).hexdigest(),
                    )
                )
            audit(s, tenant, "tenant.initialized", tenant)

    def slot(self, start: datetime, service: str) -> tuple[datetime, datetime]:
        if service not in self.business.services:
            raise DomainError("unsupported_service", 422)
        zone = ZoneInfo(self.business.timezone)
        if start.tzinfo is None or start.utcoffset() is None:
            raise DomainError("timezone_offset_required", 422)
        local = start.astimezone(zone)
        if start.replace(tzinfo=None) != local.replace(tzinfo=None):
            # Require a business-local time with the correct zone offset; catches DST gaps.
            raise DomainError("business_timezone_offset_mismatch", 422)
        wall = local.replace(tzinfo=None)
        if (
            wall.replace(tzinfo=zone, fold=0).utcoffset()
            != wall.replace(tzinfo=zone, fold=1).utcoffset()
        ):
            raise DomainError("ambiguous_or_nonexistent_wall_time", 422)
        utc = start.astimezone(UTC)
        end = utc + timedelta(minutes=self.business.services[service])
        if utc <= now() or utc > now() + timedelta(days=self.business.advance_days):
            raise DomainError("outside_booking_window", 422)
        if local.weekday() not in self.business.weekdays or local.hour < self.business.opening_hour:
            raise DomainError("business_closed", 422)
        if (
            end.astimezone(zone).date() != local.date()
            or (
                end.astimezone(zone).hour * 60 + end.astimezone(zone).minute
                > self.business.closing_hour * 60
            )
            or (local.hour * 60 + local.minute - self.business.opening_hour * 60)
            % self.business.slot_minutes
            or local.second
            or local.microsecond
        ):
            raise DomainError("invalid_slot", 422)
        return utc, end

    def free(
        self, s: Session, tenant: str, start: datetime, end: datetime, exclude: str | None = None
    ) -> bool:
        query = select(Appointment.id).where(
            Appointment.tenant_id == tenant,
            Appointment.status.not_in(["cancelled", "rejected"]),
            or_(
                and_(Appointment.start < end, Appointment.end > start),
                and_(
                    cast(Appointment.desired["start"].as_string(), DateTime(timezone=True)) < end,
                    cast(Appointment.desired["end"].as_string(), DateTime(timezone=True)) > start,
                ),
            ),
        )
        if exclude:
            query = query.where(Appointment.id != exclude)
        if s.scalar(query.limit(1)):
            return False
        return self.calendar.available(start.isoformat(), end.isoformat(), exclude, session=s)

    def require_active_call(self, session: Session, tenant: str, call_id: str) -> None:
        """Called within the same tenant-locked transaction as the protected work."""
        call = session.scalar(select(Call).where(Call.id == call_id, Call.tenant_id == tenant))
        if not call:
            raise DomainError("call_binding_invalid", 403)
        if call.state == "ended":
            raise DomainError("call_not_active", 403)

    def availability(
        self, tenant: str, start: datetime, service: str, call_id: str | None = None
    ) -> dict[str, Any]:
        begin, end = self.slot(start, service)
        with self.sessions.begin() as s:
            if call_id:
                tenant_lock(s, tenant)
                self.require_active_call(s, tenant, call_id)
            return {
                "available": self.free(s, tenant, begin, end),
                "start": begin.isoformat(),
                "end": end.isoformat(),
                "timezone": self.business.timezone,
                "reservation_required": True,
            }

    def appointment(self, tenant: str, booking_id: str) -> dict[str, Any]:
        with self.sessions() as s:
            row = s.scalar(
                select(Appointment).where(
                    Appointment.tenant_id == tenant, Appointment.id == booking_id
                )
            )
            if not row:
                raise DomainError("booking_not_found", 404)
            return booking_view(row)

    def operation(self, s: Session, tenant: str, key: str, digest: str) -> dict[str, Any] | None:
        row = s.scalar(select(Operation).where(Operation.tenant_id == tenant, Operation.key == key))
        if row and row.fingerprint != digest:
            raise DomainError("idempotency_input_conflict")
        return row.result if row else None

    def enqueue(
        self, s: Session, tenant: str, kind: str, key: str, payload: dict[str, Any]
    ) -> None:
        existing = s.scalar(
            select(Job).where(Job.tenant_id == tenant, Job.kind == kind, Job.operation_key == key)
        )
        if existing:
            if existing.payload != payload:
                raise DomainError("outbox_payload_conflict")
            return
        s.add(Job(id=identity(), tenant_id=tenant, kind=kind, operation_key=key, payload=payload))

    def book(self, tenant: str, value: BookingInput) -> dict[str, Any]:
        if not value.confirmed:
            raise DomainError("explicit_confirmation_required", 422)
        digest = fingerprint(value.model_dump(mode="json"))
        with self.sessions.begin() as s:
            tenant_lock(s, tenant)
            if value.call_id:
                self.require_active_call(s, tenant, value.call_id)
            existing = self.operation(s, tenant, value.operation_id, digest)
            if existing:
                return existing
            start, end = self.slot(value.start, value.service)
            if not self.free(s, tenant, start, end):
                raise DomainError("slot_unavailable")
            contact = s.scalar(
                select(Contact).where(Contact.tenant_id == tenant, Contact.email == value.email)
            )
            if not contact:
                contact = Contact(
                    id=identity(),
                    tenant_id=tenant,
                    name=value.name,
                    email=value.email,
                    phone=value.phone,
                )
                s.add(contact)
                s.flush()
            else:
                contact.name, contact.phone = value.name, value.phone
            row = Appointment(
                id=identity(),
                tenant_id=tenant,
                contact_id=contact.id,
                call_id=value.call_id,
                service=value.service,
                start=start,
                end=end,
                status="pending",
                revision=1,
            )
            s.add(row)
            s.flush()
            result = {"booking_id": row.id, "accepted": True}
            s.add(
                Operation(
                    id=identity(),
                    tenant_id=tenant,
                    key=value.operation_id,
                    fingerprint=digest,
                    result=result,
                )
            )
            self.enqueue(
                s,
                tenant,
                "calendar",
                row.id + "-1",
                {
                    "booking_id": row.id,
                    "revision": 1,
                    "intent": {
                        "start": start.isoformat(),
                        "end": end.isoformat(),
                        "status": "confirmed",
                        "service": row.service,
                        "revision": 1,
                    },
                    "contact": {"name": value.name, "email": value.email, "phone": value.phone},
                },
            )
            audit(s, tenant, "booking.accepted", row.id)
            return result

    def change(
        self, tenant: str, booking_id: str, value: ChangeInput, contact_id: str | None = None
    ) -> dict[str, Any]:
        if not value.confirmed:
            raise DomainError("explicit_confirmation_required", 422)
        digest = fingerprint({**value.model_dump(mode="json"), "booking_id": booking_id})
        with self.sessions.begin() as s:
            tenant_lock(s, tenant)
            row = s.scalar(
                select(Appointment).where(
                    Appointment.id == booking_id, Appointment.tenant_id == tenant
                )
            )
            if not row:
                raise DomainError("booking_not_found", 404)
            if contact_id is not None and row.contact_id != contact_id:
                raise DomainError("caller_identity_unverified", 403)
            existing = self.operation(s, tenant, value.operation_id, digest)
            if existing:
                return existing
            cancellable_pending = value.action == "cancel" and row.status in {
                "pending",
                "reschedule_pending",
                "cancel_pending",
            }
            if row.revision != value.expected_revision or (
                row.status != "confirmed" and not cancellable_pending
            ):
                raise DomainError("booking_revision_or_state_conflict")
            if value.action == "reschedule":
                if value.start is None:
                    raise DomainError("new_start_required", 422)
                start, end = self.slot(value.start, row.service)
                if not self.free(s, tenant, start, end, row.external_id):
                    raise DomainError("slot_unavailable")
                row.desired = {
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "status": "confirmed",
                }
            else:
                row.desired = {"status": "cancelled"}
            row.status = value.action + "_pending"
            row.revision += 1
            result = {"booking_id": row.id, "accepted": True}
            s.add(
                Operation(
                    id=identity(),
                    tenant_id=tenant,
                    key=value.operation_id,
                    fingerprint=digest,
                    result=result,
                )
            )
            contact = s.get(Contact, row.contact_id)
            if not contact:
                raise DomainError("contact_not_found", 404)
            intent = {
                "start": row.start.isoformat(),
                "end": row.end.isoformat(),
                "service": row.service,
                "revision": row.revision,
                **row.desired,
            }
            self.enqueue(
                s,
                tenant,
                "calendar",
                row.id + "-" + str(row.revision),
                {
                    "booking_id": row.id,
                    "revision": row.revision,
                    "intent": intent,
                    "contact": {
                        "name": contact.name,
                        "email": contact.email,
                        "phone": contact.phone,
                    },
                },
            )
            audit(s, tenant, "booking." + value.action + ".accepted", row.id)
            return result

    def documents(self, tenant: str) -> list[dict[str, Any]]:
        with self.sessions() as s:
            return [
                {
                    "id": r.id,
                    "name": r.name,
                    "text": r.text,
                    "revision": r.revision,
                    "updated": r.updated.isoformat(),
                    "checksum": r.checksum,
                }
                for r in s.scalars(
                    select(Document).where(Document.tenant_id == tenant, Document.active.is_(True))
                )
            ]

    def validate_document(self, value: DocumentInput) -> None:
        if len(value.text.encode()) > self.settings.max_document_bytes:
            raise DomainError("document_too_large", 413)
        if "\x00" in value.text or any(ord(c) < 32 and c not in "\n\r\t" for c in value.text):
            raise DomainError("document_invalid_text", 422)

    def document(self, tenant: str, value: DocumentInput, doc_id: str | None = None) -> str:
        self.validate_document(value)
        with self.sessions.begin() as s:
            tenant_lock(s, tenant)
            row = s.scalar(
                select(Document).where(Document.tenant_id == tenant, Document.id == doc_id)
            )
            if doc_id and not row:
                raise DomainError("document_not_found", 404)
            if not row or not row.active:
                count = (
                    s.scalar(
                        select(func.count())
                        .select_from(Document)
                        .where(Document.tenant_id == tenant, Document.active.is_(True))
                    )
                    or 0
                )
                if count >= self.settings.max_documents:
                    raise DomainError("document_limit", 422)
            if row:
                if row.revision != value.expected_revision:
                    raise DomainError("document_revision_conflict")
                row.name, row.text, row.checksum = (
                    value.name,
                    value.text,
                    hashlib.sha256(value.text.encode()).hexdigest(),
                )
                row.updated, row.revision, row.active = now(), row.revision + 1, True
                row.fact_key = value.fact_key
            else:
                row = Document(
                    id=identity(),
                    tenant_id=tenant,
                    name=value.name,
                    text=value.text,
                    fact_key=value.fact_key,
                    checksum=hashlib.sha256(value.text.encode()).hexdigest(),
                )
                s.add(row)
            audit(s, tenant, "knowledge.saved", row.id)
            return row.id

    def delete_document(self, tenant: str, doc_id: str) -> None:
        with self.sessions.begin() as s:
            tenant_lock(s, tenant)
            row = s.scalar(
                select(Document).where(Document.tenant_id == tenant, Document.id == doc_id)
            )
            if not row:
                raise DomainError("document_not_found", 404)
            row.active, row.revision = False, row.revision + 1
            audit(s, tenant, "knowledge.deleted", row.id)

    def answer(self, tenant: str, query: str, call_id: str | None = None) -> dict[str, Any]:
        if not query.strip() or len(query) > self.settings.max_query_chars:
            raise DomainError("invalid_query", 422)
        with self.sessions.begin() as s:
            if call_id:
                tenant_lock(s, tenant)
                self.require_active_call(s, tenant, call_id)
            tsquery = func.plainto_tsquery(self.settings.search_language, query)
            vector = func.to_tsvector(
                self.settings.search_language, Document.name + " " + Document.text
            )
            eligible = [
                Document.tenant_id == tenant,
                Document.active.is_(True),
                Document.updated >= now() - timedelta(days=self.settings.knowledge_max_age_days),
            ]
            matching_keys = select(Document.fact_key).where(
                *eligible, Document.fact_key.is_not(None), vector.op("@@")(tsquery)
            )
            conflict = s.scalar(
                select(Document.fact_key)
                .where(*eligible, Document.fact_key.in_(matching_keys))
                .group_by(Document.fact_key)
                .having(func.count(func.distinct(Document.checksum)) > 1)
                .limit(1)
            )
            if conflict:
                return {
                    "status": "abstained",
                    "answer": self.business.messages["conflict"],
                    "sources": [],
                }
            rows = list(
                s.scalars(
                    select(Document)
                    .where(
                        Document.tenant_id == tenant,
                        Document.active.is_(True),
                        Document.updated
                        >= now() - timedelta(days=self.settings.knowledge_max_age_days),
                        vector.op("@@")(tsquery),
                    )
                    .order_by(func.ts_rank(vector, tsquery).desc())
                    .limit(self.settings.search_limit)
                )
            )
            facts: dict[str, set[str]] = {}
            for row in rows:
                if row.fact_key:
                    facts.setdefault(row.fact_key, set()).add(row.checksum)
            if any(len(values) > 1 for values in facts.values()):
                return {
                    "status": "abstained",
                    "answer": self.business.messages["conflict"],
                    "sources": [],
                }
            if not rows:
                return {
                    "status": "abstained",
                    "answer": self.business.messages["missing"],
                    "sources": [],
                }
            # Extractive data only. No LLM/tool executor reads documents as instructions.
            return {
                "status": "answered",
                "answer": "\n".join(r.text for r in rows),
                "sources": [
                    {"id": r.id, "name": r.name, "revision": r.revision, "checksum": r.checksum}
                    for r in rows
                ],
                "authority": "data_only",
            }

    def save_agent(self, tenant: str, value: AgentInput) -> dict[str, Any]:
        with self.sessions.begin() as s:
            tenant_lock(s, tenant)
            row = s.scalar(
                select(Record).where(
                    Record.tenant_id == tenant, Record.kind == "agent", Record.key == "draft"
                )
            )
            if not row or row.revision != value.expected_revision:
                raise DomainError("agent_revision_conflict")
            row.value = value.model_dump(exclude={"expected_revision"})
            row.revision += 1
            audit(s, tenant, "agent.draft.saved", row.id)
            return {**row.value, "revision": row.revision}

    def replay(self, tenant: str, job_id: str) -> None:
        with self.sessions.begin() as s:
            row = s.scalar(
                select(Job).where(Job.tenant_id == tenant, Job.id == job_id).with_for_update()
            )
            if not row:
                raise DomainError("job_not_found", 404)
            if row.status not in {"dead", "failed"}:
                raise DomainError("job_requires_reconciliation_or_already_active")
            row.status, row.next_run, row.attempts = "pending", now(), 0
            audit(s, tenant, "job.replayed", row.id)

    def evaluate(
        self,
        tenant: str,
        parity: Callable[[str], str] | None = None,
        positive_booking: Callable[[datetime, str], str] | None = None,
    ) -> dict[str, Any]:
        data = self.evaluations
        results = []
        start = (now() + timedelta(days=1)).astimezone(ZoneInfo(self.business.timezone))
        start = start.replace(hour=self.business.opening_hour, minute=0, second=0, microsecond=0)
        while start.weekday() not in self.business.weekdays:
            start += timedelta(days=1)
        service = next(iter(self.business.services))
        for case in data.cases:
            try:
                if case.kind == "knowledge":
                    actual = str(self.answer(tenant, case.query)["status"])
                elif case.kind == "isolation":
                    actual = str(self.answer(identity(), case.query)["status"])
                elif case.kind == "confirmation":
                    self.book(
                        tenant,
                        BookingInput(
                            **data.contact,
                            operation_id=identity(),
                            service=service,
                            start=start,
                            confirmed=False,
                        ),
                    )
                    actual = "unexpected_acceptance"
                elif case.kind == "invalid_slot":
                    self.slot(start.replace(tzinfo=None), service)
                    actual = "unexpected_acceptance"
                elif case.kind == "booking":
                    actual = (
                        positive_booking(start, service) if positive_booking else "not_exercised"
                    )
                elif case.kind == "adversarial_retrieval":
                    isolated = "evaluation-" + identity()
                    self.seed(isolated)
                    doc_id = self.document(isolated, data.adversarial_document)
                    before = self.snapshot(isolated)["appointments"]
                    try:
                        answer = self.answer(isolated, case.query)
                        grounded = (
                            answer.get("status") == "answered"
                            and answer.get("authority") == "data_only"
                            and any(source["id"] == doc_id for source in answer["sources"])
                            and before == self.snapshot(isolated)["appointments"]
                        )
                        actual = "grounded_data_only" if grounded else "unsafe_or_not_retrieved"
                    finally:
                        self.delete_document(isolated, doc_id)
                else:
                    actual = parity(case.query) if parity else "not_exercised"
            except DomainError as exc:
                actual = exc.code
            results.append(
                {
                    "id": case.id,
                    "kind": case.kind,
                    "expected": case.expected,
                    "actual": actual,
                    "passed": case.expected == actual,
                }
            )
        with self.sessions.begin() as s:
            audit(s, tenant, "evaluation.executed", str(data.revision))
        return {"revision": data.revision, "cases": results, "acoustic": "not_tested"}

    def snapshot(self, tenant: str) -> dict[str, Any]:
        with self.sessions() as s:

            def rows(model: Any) -> Any:
                return s.scalars(
                    select(model)
                    .where(model.tenant_id == tenant)
                    .limit(self.settings.max_records_per_page)
                )

            def count(model: Any) -> int:
                return int(
                    s.scalar(
                        select(func.count()).select_from(model).where(model.tenant_id == tenant)
                    )
                    or 0
                )

            agent = s.scalar(
                select(Record).where(Record.tenant_id == tenant, Record.kind == "agent")
            )
            return {
                "appointments": [booking_view(r) for r in rows(Appointment)],
                "contacts": [
                    {
                        "id": r.id,
                        "name": r.name,
                        "email": r.email,
                        "phone": r.phone,
                        "notes": r.notes,
                    }
                    for r in rows(Contact)
                ],
                "jobs": [
                    {
                        "id": r.id,
                        "kind": r.kind,
                        "status": r.status,
                        "attempts": r.attempts,
                        "detail": r.detail,
                        "booking_id": r.payload.get("booking_id"),
                        "receipt": r.receipt,
                    }
                    for r in rows(Job)
                ],
                "calls": [
                    {
                        "id": r.id,
                        "provider": r.provider,
                        "state": r.state,
                        "transcript": r.transcript,
                        "date": r.created.isoformat(),
                    }
                    for r in rows(Call)
                ],
                "audit": [
                    {
                        "id": r.id,
                        "action": r.action,
                        "target": r.target,
                        "date": r.created.isoformat(),
                    }
                    for r in rows(Audit)
                ],
                "agent": {**agent.value, "revision": agent.revision} if agent else None,
                "documents": [
                    {
                        "id": r.id,
                        "name": r.name,
                        "text": r.text,
                        "revision": r.revision,
                        "updated": r.updated.isoformat(),
                        "checksum": r.checksum,
                    }
                    for r in s.scalars(
                        select(Document)
                        .where(Document.tenant_id == tenant, Document.active.is_(True))
                        .limit(self.settings.max_records_per_page)
                    )
                ],
                "record_limit": self.settings.max_records_per_page,
                "counts": {
                    model.__tablename__: count(model) for model in [Appointment, Contact, Call, Job]
                },
                "integrations": {
                    "calendar": "live-enabled" if self.settings.provider.enabled else "local",
                    "crm": "live-enabled" if self.settings.provider.enabled else "local",
                    "vapi": (
                        "read-only-access-verified"
                        if self.settings.provider.vapi_owner_resolved
                        else "owner-resolution-required"
                    ),
                    "followup": self.settings.followup_transport,
                },
                "evaluation_fixtures": [
                    {"id": record.key, **record.value}
                    for record in s.scalars(
                        select(Record)
                        .where(
                            Record.tenant_id == tenant,
                            Record.kind == "evaluation_fixture",
                        )
                        .order_by(Record.value["status"].as_string().desc(), Record.key)
                        .limit(self.settings.max_records_per_page)
                    )
                ],
                "synthetic": not self.settings.provider.enabled,
            }
