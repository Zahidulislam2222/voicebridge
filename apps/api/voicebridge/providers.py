"""Platform-specific authenticated event/tool envelopes; business logic is shared."""

import hashlib
import hmac
import json
import re
import secrets
from datetime import datetime, timedelta
from typing import Any

from pydantic import ValidationError
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from .connectors import Delivery, LocalCalendar
from .contracts import (
    AgentInput,
    AvailabilityInput,
    BookingInput,
    BookingLookupInput,
    CallIntentBinding,
    ChangeInput,
    DomainError,
    QuestionInput,
)
from .db import Appointment, Call, Inbox, Job, Record, now, tenant_lock
from .protocol import (
    CALL_CAPABILITY_METADATA_KEY,
    CALL_INTENT_KIND,
    CALL_INTENT_PREFIX,
    EVALUATION_CALENDAR_PREFIX,
    EVALUATION_TENANT_PREFIX,
    RETELL_TERMINAL,
    TRANSCRIPT_SPEAKERS,
    VAPI_TERMINAL,
)
from .service import Service, audit, identity
from .worker import Worker


def retell_verify(body: bytes, signature: str, key: str, tolerance: int) -> bool:
    match = re.fullmatch(r"v=(\d+),d=([0-9a-f]{64})", signature)
    if not match or not key:
        return False
    stamp, digest = match.groups()
    if abs(now().timestamp() * 1000 - int(stamp)) > tolerance * 1000:
        return False
    expected = hmac.new(key.encode(), body + stamp.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, digest)


class Providers:
    def __init__(self, service: Service, worker: Worker) -> None:
        self.service, self.worker = service, worker

    def evaluate(self, tenant: str) -> dict[str, Any]:
        if self.service.settings.provider.enabled:
            raise DomainError("synthetic_evaluation_required", 403)

        def parity(query: str) -> str:
            outputs = []
            for provider in ("retell", "vapi"):
                body: dict[str, Any]
                ended: dict[str, Any]
                external = "evaluation-" + identity()
                agent = self.service.evaluations.agent_id
                registered = self.register(tenant, provider, external, agent)
                args = {"query": query}
                if provider == "retell":
                    body = {
                        "call": {"call_id": external, "agent_id": agent},
                        "name": "answer_question",
                        "args": args,
                    }
                    output = self.tools(provider, body, registered["capability"])
                    ended = {"call": body["call"], "event": "call_ended"}
                else:
                    body = {
                        "message": {
                            "type": "tool-calls",
                            "call": {"id": external, "assistantId": agent},
                            "toolCallList": [
                                {
                                    "id": "evaluation-tool",
                                    "function": {"name": "answer_question", "arguments": args},
                                }
                            ],
                        }
                    }
                    result = self.tools(provider, body, registered["capability"])
                    output = json.loads(result["results"][0]["result"])
                    ended = {
                        "message": {"type": "end-of-call-report", "call": body["message"]["call"]}
                    }
                outputs.append(output)
                self.event(provider, ended, registered["capability"])
            return "equal" if outputs[0] == outputs[1] else "different"

        def positive(start: datetime, service: str) -> str:
            fixture_id = identity()
            isolated = EVALUATION_TENANT_PREFIX + fixture_id
            with self.service.sessions.begin() as session:
                session.add(
                    Record(
                        id=identity(),
                        tenant_id=tenant,
                        kind="evaluation_fixture",
                        key=fixture_id,
                        value={"status": "pending", "booking_ids": [], "detail": "fixture_started"},
                    )
                )
            runner = self.fixture_provider(tenant, fixture_id)
            runner.service.seed(isolated)
            statuses: list[str] = []
            try:
                outcome = self.positive_fixture(runner, isolated, start, service, statuses)
            finally:
                cleanup = self.cleanup_fixture(tenant, fixture_id)
            return outcome if cleanup["status"] == "completed" else "evaluation_cleanup_pending"

        return self.service.evaluate(tenant, parity, positive)

    def positive_fixture(
        self,
        runner: "Providers",
        isolated: str,
        start: datetime,
        service: str,
        statuses: list[str],
    ) -> str:
        for provider in ("retell", "vapi"):
            external = "evaluation-" + identity()
            agent = self.service.evaluations.agent_id
            registered = runner.register(isolated, provider, external, agent)
            args = {
                **self.service.evaluations.contact,
                "operation_id": identity(),
                "start": start.isoformat(),
                "service": service,
                "confirmed": True,
            }
            body: dict[str, Any]
            ended: dict[str, Any]
            if provider == "retell":
                body = {
                    "call": {"call_id": external, "agent_id": agent},
                    "name": "create_booking",
                    "args": args,
                }
                ended = {"call": body["call"], "event": "call_ended"}
            else:
                body = {
                    "message": {
                        "type": "tool-calls",
                        "call": {"id": external, "assistantId": agent},
                        "toolCallList": [
                            {
                                "id": "evaluation-tool",
                                "function": {"name": "create_booking", "arguments": args},
                            }
                        ],
                    }
                }
                ended = {"message": {"type": "end-of-call-report", "call": body["message"]["call"]}}
            try:
                result = runner.tools(provider, body, registered["capability"])
                if provider == "vapi":
                    tool = result["results"][0]
                    if "error" in tool:
                        raise DomainError(tool["error"])
                    result = json.loads(tool["result"])
                statuses.append(str(result["status"]))
                # Release each successful slot before the next adapter.
                if result["status"] == "confirmed":
                    runner.service.change(
                        isolated,
                        result["id"],
                        ChangeInput(
                            operation_id=identity(),
                            action="cancel",
                            confirmed=True,
                            expected_revision=result["revision"],
                        ),
                    )
                    runner.drain_calendar(isolated, result["id"])
            finally:
                runner.event(provider, ended, registered["capability"])
        return "confirmed" if statuses == ["confirmed", "confirmed"] else "booking_failed"

    def fixture_provider(self, tenant: str, fixture_id: str) -> "Providers":
        if self.service.settings.provider.enabled:
            raise DomainError("synthetic_evaluation_required", 403)
        with self.service.sessions() as session:
            fixture = session.scalar(
                select(Record).where(
                    Record.tenant_id == tenant,
                    Record.kind == "evaluation_fixture",
                    Record.key == fixture_id,
                )
            )
            if not fixture:
                raise DomainError("evaluation_fixture_not_found", 404)
        settings = self.service.settings.model_copy(
            update={
                "tenant_id": EVALUATION_TENANT_PREFIX + fixture_id,
                "followup_transport": "capture",
            }
        )
        calendar = LocalCalendar(self.service.sessions, EVALUATION_CALENDAR_PREFIX + fixture_id)
        service = Service(settings, self.service.sessions, calendar)
        return Providers(service, Worker(service, Delivery(settings, self.service.sessions)))

    def cleanup_fixture(self, tenant: str, fixture_id: str) -> dict[str, Any]:
        runner = self.fixture_provider(tenant, fixture_id)
        isolated = runner.service.settings.tenant_id
        with self.service.sessions.begin() as session:
            fixture = session.scalar(
                select(Record)
                .where(
                    Record.tenant_id == tenant,
                    Record.kind == "evaluation_fixture",
                    Record.key == fixture_id,
                )
                .with_for_update()
            )
            if not fixture:
                raise DomainError("evaluation_fixture_not_found", 404)
            bookings = []
            cursor = ""
            # A dashboard page limit cannot truncate a cleanup obligation.
            # Keyset pages inspect every fixture booking with bounded queries.
            with runner.service.sessions() as source:
                while True:
                    page = list(
                        source.scalars(
                            select(Appointment)
                            .where(Appointment.tenant_id == isolated, Appointment.id > cursor)
                            .order_by(Appointment.id)
                            .limit(self.service.settings.max_records_per_page)
                        )
                    )
                    if not page:
                        break
                    bookings.extend(page)
                    cursor = page[-1].id
            pending = False
            for booking in bookings:
                if booking.status != "cancelled":
                    if booking.status != "cancel_pending":
                        runner.service.change(
                            isolated,
                            booking.id,
                            ChangeInput(
                                operation_id="evaluation-cleanup-"
                                + booking.id
                                + "-"
                                + str(booking.revision),
                                action="cancel",
                                confirmed=True,
                                expected_revision=booking.revision,
                            ),
                        )
                    with runner.service.sessions() as source:
                        revision = runner.service.appointment(isolated, booking.id)["revision"]
                        job = source.scalar(
                            select(Job)
                            .where(
                                Job.tenant_id == isolated,
                                Job.kind == "calendar",
                                Job.payload["booking_id"].as_string() == booking.id,
                                Job.payload["revision"].as_integer() == revision,
                            )
                            .limit(1)
                        )
                    if job:
                        if job.status in {"reconcile", "unknown"}:
                            runner.worker.reconcile(isolated, job.id)
                        elif job.status in {"failed", "dead"}:
                            runner.service.replay(isolated, job.id)
                        runner.worker.run_one(job.id)
                        with runner.service.sessions() as source:
                            current = source.get(Job, job.id)
                            if current and current.status == "reconcile":
                                runner.worker.reconcile(isolated, job.id)
                                runner.worker.run_one(job.id)
                current_booking = runner.service.appointment(isolated, booking.id)
                receipt = runner.service.calendar.get(booking.id)
                if (
                    current_booking["status"] != "cancelled"
                    or not receipt
                    or receipt.get("status") != "cancelled"
                    or receipt.get("revision") != current_booking["revision"]
                ):
                    pending = True
            fixture.value = {
                "status": "pending" if pending else "completed",
                "booking_ids": [booking.id for booking in bookings],
                "detail": "cancellation_unverified" if pending else "cancellation_verified",
            }
            audit(session, tenant, "evaluation.cleanup." + fixture.value["status"], fixture_id)
            return {"id": fixture_id, **fixture.value}

    def prepare_intent(self, tenant: str, provider: str) -> dict[str, Any]:
        if provider not in {"retell", "vapi"}:
            raise DomainError("invalid_call_provider", 422)
        agent_id = getattr(self.service.profiles, provider).agent_id
        if not agent_id:
            raise DomainError("provider_profile_not_configured", 403)
        capability = secrets.token_urlsafe(32)
        intent_id = CALL_INTENT_PREFIX + identity()
        expires = now() + timedelta(seconds=self.service.settings.call_intent_seconds)
        with self.service.sessions.begin() as session:
            tenant_lock(session, tenant)
            pending = (Record.tenant_id == tenant, Record.kind == CALL_INTENT_KIND)
            session.execute(
                delete(Record).where(
                    *pending, Record.value["expires_at"].as_float() <= now().timestamp()
                )
            )
            count = session.scalar(select(func.count()).select_from(Record).where(*pending))
            if count is not None and count >= self.service.settings.max_pending_call_intents:
                raise DomainError("call_intent_capacity_reached", 429)
            session.add(
                Record(
                    id=identity(),
                    tenant_id=tenant,
                    kind=CALL_INTENT_KIND,
                    key=intent_id,
                    value={
                        "provider": provider,
                        "agent_id": agent_id,
                        "digest": hashlib.sha256(capability.encode()).hexdigest(),
                        "expires_at": expires.timestamp(),
                    },
                )
            )
            audit(session, tenant, "call.intent.prepared", intent_id)
        return {
            "intent_id": intent_id,
            "capability": capability,
            "provider": provider,
            "agent_id": agent_id,
            "expires_at": expires.isoformat(),
        }

    def bind_intent(self, tenant: str, value: CallIntentBinding) -> dict[str, str]:
        if not value.intent_id.startswith(CALL_INTENT_PREFIX):
            raise DomainError("call_intent_not_found", 404)
        try:
            with self.service.sessions.begin() as session:
                tenant_lock(session, tenant)
                bound = session.get(Call, value.intent_id)
                if bound:
                    if bound.tenant_id != tenant:
                        raise DomainError("call_intent_not_found", 404)
                    if bound.external_id != value.external_id:
                        raise DomainError("call_intent_already_bound", 409)
                    return {"call_id": bound.id}
                intent = session.scalar(
                    select(Record).where(
                        Record.tenant_id == tenant,
                        Record.kind == CALL_INTENT_KIND,
                        Record.key == value.intent_id,
                    )
                )
                if not intent:
                    raise DomainError("call_intent_not_found", 404)
                if intent.value["expires_at"] <= now().timestamp():
                    raise DomainError("call_intent_expired", 403)
                if session.scalar(
                    select(Call).where(
                        Call.provider == intent.value["provider"],
                        Call.external_id == value.external_id,
                    )
                ):
                    raise DomainError("call_already_registered", 409)
                session.add(
                    Call(
                        id=value.intent_id,
                        tenant_id=tenant,
                        provider=intent.value["provider"],
                        external_id=value.external_id,
                        agent_id=intent.value["agent_id"],
                        capability_digest=intent.value["digest"],
                    )
                )
                session.delete(intent)
                audit(session, tenant, "call.intent.bound", value.intent_id)
        except IntegrityError as exc:
            raise DomainError("call_already_registered", 409) from exc
        return {"call_id": value.intent_id}

    def register(
        self, tenant: str, provider: str, external_id: str, agent_id: str
    ) -> dict[str, str]:
        if (
            provider not in {"retell", "vapi"}
            or not external_id
            or len(external_id) > 100
            or not agent_id
            or len(agent_id) > 100
        ):
            raise DomainError("invalid_call_registration", 422)
        capability = secrets.token_urlsafe(32)
        with self.service.sessions.begin() as s:
            tenant_lock(s, tenant)
            if s.scalar(
                select(Call).where(Call.provider == provider, Call.external_id == external_id)
            ):
                raise DomainError("call_already_registered")
            call = Call(
                id=identity(),
                tenant_id=tenant,
                provider=provider,
                external_id=external_id,
                agent_id=agent_id,
                capability_digest=hashlib.sha256(capability.encode()).hexdigest(),
            )
            s.add(call)
            audit(s, tenant, "call.registered", call.id)
        return {"call_id": call.id, "capability": capability}

    def binding(
        self,
        provider: str,
        external: str,
        agent: str,
        capability: str,
        *,
        allow_terminal: bool = False,
    ) -> tuple[str, str]:
        if (
            not isinstance(external, str)
            or not external
            or len(external) > 100
            or not isinstance(agent, str)
            or not agent
            or len(agent) > 100
            or not isinstance(capability, str)
            or not capability
        ):
            raise DomainError("call_binding_invalid", 403)
        with self.service.sessions() as s:
            call = s.scalar(
                select(Call).where(Call.provider == provider, Call.external_id == external)
            )
            if (
                not call
                or call.agent_id != agent
                or not hmac.compare_digest(
                    call.capability_digest, hashlib.sha256(capability.encode()).hexdigest()
                )
            ):
                raise DomainError("call_binding_invalid", 403)
            if call.state == "ended" and not allow_terminal:
                raise DomainError("call_not_active", 403)
            return call.tenant_id, call.id

    def envelope_capability(self, provider: str, body: dict[str, Any], supplied: str | None) -> str:
        # The HTTP boundary invokes this only after raw provider authentication.
        if supplied is not None:
            return supplied
        if not self.service.settings.provider_metadata_capability:
            return ""
        call = body["call"] if provider == "retell" else body["message"]["call"]
        if not isinstance(call, dict):
            raise DomainError("invalid_provider_metadata", 422)
        metadata = call.get("metadata", {})
        if not isinstance(metadata, dict):
            raise DomainError("invalid_provider_metadata", 422)
        value = metadata.get(CALL_CAPABILITY_METADATA_KEY, "")
        if not isinstance(value, str):
            raise DomainError("invalid_provider_metadata", 422)
        return value

    def final_transcript(
        self, provider: str, payload: dict[str, Any]
    ) -> list[dict[str, str]] | None:
        if provider == "retell":
            rows, content_key = payload.get("transcript_object"), "content"
        else:
            artifact = payload.get("artifact", {})
            if not isinstance(artifact, dict):
                raise DomainError("invalid_provider_transcript", 422)
            payload = artifact
            rows, content_key = artifact.get("messages"), "message"
        if rows is None:
            text = payload.get("transcript")
            if text is None:
                return None
            if not isinstance(text, str):
                raise DomainError("invalid_provider_transcript", 422)
            return [{"speaker": "transcript", "text": text}] if text.strip() else []
        if not isinstance(rows, list):
            raise DomainError("invalid_provider_transcript", 422)
        result = []
        for row in rows:
            if not isinstance(row, dict):
                raise DomainError("invalid_provider_transcript", 422)
            role = row.get("role")
            if not isinstance(role, str):
                raise DomainError("invalid_provider_transcript", 422)
            speaker = TRANSCRIPT_SPEAKERS[provider].get(role)
            if speaker is None:
                continue  # System prompts and tool arguments are not spoken turns.
            text = row.get(content_key)
            if not isinstance(text, str):
                raise DomainError("invalid_provider_transcript", 422)
            if text.strip():
                result.append({"speaker": speaker, "text": text})
        return result

    def event(self, provider: str, body: dict[str, Any], capability: str) -> dict[str, Any]:
        if provider == "retell":
            call_data, event = body["call"], body["event"]
            external, agent = call_data["call_id"], call_data["agent_id"]
            terminal = event in RETELL_TERMINAL
        else:
            message = body["message"]
            call_data, event = message["call"], message["type"]
            external, agent = call_data["id"], call_data["assistantId"]
            terminal = event in VAPI_TERMINAL
            terminal = terminal or (event == "status-update" and message.get("status") == "ended")
        tenant, call_id = self.binding(provider, external, agent, capability, allow_terminal=True)
        transcript = (
            self.final_transcript(provider, call_data if provider == "retell" else message)
            if event in (RETELL_TERMINAL if provider == "retell" else VAPI_TERMINAL)
            else None
        )
        event_key = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        with self.service.sessions.begin() as s:
            tenant_lock(s, tenant)
            if s.scalar(
                select(Inbox).where(Inbox.provider == provider, Inbox.event_key == event_key)
            ):
                return {"accepted": True, "duplicate": True}
            call = s.get(Call, call_id)
            if not call:
                raise DomainError("call_binding_invalid", 403)
            s.add(
                Inbox(
                    id=identity(),
                    tenant_id=tenant,
                    provider=provider,
                    event_key=event_key,
                    call_id=call_id,
                    event=event,
                )
            )
            if terminal:
                call.state = "ended"
            elif call.state != "ended":
                call.state = "active"
            if transcript and not call.transcript:
                call.transcript = transcript
            audit(s, tenant, "provider.event.accepted", call.id)
        return {"accepted": True, "duplicate": False}

    def tools(self, provider: str, body: dict[str, Any], capability: str) -> dict[str, Any]:
        if provider == "retell":
            c = body["call"]
            tenant, call_id = self.binding(provider, c["call_id"], c["agent_id"], capability)
            return self.invoke(tenant, body["name"], body["args"], call_id)
        message = body["message"]
        c = message["call"]
        tenant, call_id = self.binding(provider, c["id"], c["assistantId"], capability)
        if message["type"] != "tool-calls":
            raise DomainError("invalid_vapi_tool_envelope", 422)
        results = []
        for tool in message["toolCallList"]:
            try:
                function = tool["function"]
                args = function["arguments"]
                if isinstance(args, str):
                    args = json.loads(args)
                result = self.invoke(tenant, function["name"], args, call_id)
                results.append({"toolCallId": tool["id"], "result": json.dumps(result)})
            except DomainError as exc:
                results.append({"toolCallId": tool["id"], "error": exc.code})
            except (ValidationError, KeyError, ValueError, TypeError):
                results.append({"toolCallId": tool["id"], "error": "invalid_tool_arguments"})
        return {"results": results}

    def invoke(
        self,
        tenant: str,
        name: str,
        args: dict[str, Any],
        call_id: str | None = None,
        management: bool = False,
    ) -> dict[str, Any]:
        # Parse strict schemas and reject surplus fields, including caller tenant IDs.
        if not isinstance(args, dict):
            raise DomainError("invalid_tool_arguments", 422)
        if name == "check_availability":
            availability = AvailabilityInput.model_validate(args)
            return self.service.availability(
                tenant, availability.start, availability.service, call_id
            )
        if name == "answer_question":
            question = QuestionInput.model_validate(args)
            return self.service.answer(tenant, question.query, call_id)
        if name == "create_booking":
            if "call_id" in args:
                raise DomainError("caller_cannot_choose_call", 403)
            value = BookingInput.model_validate({**args, "call_id": call_id})
            result = self.service.book(tenant, value)
            self.drain_calendar(tenant, result["booking_id"])
            booking = self.service.appointment(tenant, result["booking_id"])
            return {
                **booking,
                "message": self.service.business.messages[
                    "confirmed" if booking["status"] == "confirmed" else "pending"
                ],
            }
        if name in {"get_booking", "change_booking"} and call_id:
            # Knowing a booking ID or phone/email is not verified caller identity.
            raise DomainError("caller_identity_unverified", 403)
        if name == "get_booking":
            lookup = BookingLookupInput.model_validate(args)
            return self.service.appointment(tenant, lookup.booking_id)
        if name == "change_booking":
            booking_id = args.get("booking_id")
            if not isinstance(booking_id, str):
                raise DomainError("booking_id_required", 422)
            change_value = ChangeInput.model_validate(
                {k: v for k, v in args.items() if k != "booking_id"}
            )
            result = self.service.change(tenant, booking_id, change_value)
            self.drain_calendar(tenant, result["booking_id"])
            return self.service.appointment(tenant, booking_id)
        if management:
            if name == "get_state" and not args:
                return self.service.snapshot(tenant)
            if name == "get_agent_draft" and not args:
                return self.service.snapshot(tenant)["agent"]  # type: ignore[no-any-return]
            if name == "save_agent_draft":
                return self.service.save_agent(tenant, AgentInput.model_validate(args))
            if name == "run_evaluations" and not args:
                return self.evaluate(tenant)
            if name == "promote_agent":
                raise DomainError("provider_promotion_requires_separate_approval", 403)
        raise DomainError("tool_not_allowed", 403)

    def drain_calendar(self, tenant: str, booking_id: str) -> None:
        with self.service.sessions() as s:
            job = s.scalar(
                select(Job).where(
                    Job.tenant_id == tenant,
                    Job.kind == "calendar",
                    Job.payload["booking_id"].as_string() == booking_id,
                    Job.status.in_(["pending", "failed"]),
                )
            )
            job_id = job.id if job else None
        if job_id:
            self.worker.run_one(job_id)
