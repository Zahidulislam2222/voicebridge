from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi import FastAPI
from sqlalchemy import select
from voicebridge.contracts import BookingInput, ChangeInput, DomainError
from voicebridge.db import Job, now


def request(app: FastAPI, operation: str = "test-operation", hour: int = 10) -> BookingInput:
    zone = ZoneInfo(app.state.service.business.timezone)
    day = now().astimezone(zone) + timedelta(days=2)
    while day.weekday() not in app.state.service.business.weekdays:
        day += timedelta(days=1)
    return BookingInput(
        operation_id=operation,
        name="Test customer",
        phone="+15555550123",
        email="customer@voicebridge.invalid",
        service="Appliance repair",
        start=day.replace(hour=hour, minute=0, second=0, microsecond=0),
        confirmed=True,
    )


def confirmed(app: FastAPI) -> str:
    result = app.state.service.book("northline", request(app))
    app.state.providers.drain_calendar("northline", result["booking_id"])
    return str(result["booking_id"])


def test_confirmation_is_required(app: FastAPI) -> None:
    with pytest.raises(DomainError, match="explicit_confirmation_required"):
        app.state.service.book("northline", request(app).model_copy(update={"confirmed": False}))


def test_stable_operation_and_payload_conflict(app: FastAPI) -> None:
    s = app.state.service
    value = request(app)
    assert s.book("northline", value) == s.book("northline", value)
    with pytest.raises(DomainError, match="idempotency_input_conflict"):
        s.book("northline", value.model_copy(update={"name": "Different"}))


def test_concurrent_overlapping_reservations(app: FastAPI) -> None:
    def attempt(index: int) -> str:
        try:
            app.state.service.book("northline", request(app, "parallel-" + str(index)))
            return "accepted"
        except DomainError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(attempt, range(16)))
    assert results.count("accepted") == 1
    assert results.count("slot_unavailable") == 15


def test_calendar_receipt_and_atomic_outbox(app: FastAPI) -> None:
    key = confirmed(app)
    assert app.state.service.appointment("northline", key)["status"] == "confirmed"
    assert app.state.service.calendar.get(key)["status"] == "confirmed"
    jobs = app.state.service.snapshot("northline")["jobs"]
    assert sorted(j["kind"] for j in jobs) == ["calendar", "crm", "followup"]


def test_timeout_after_write_does_not_false_confirm(app: FastAPI) -> None:
    app.state.service.calendar.timeout_after_write = True
    value = app.state.service.book("northline", request(app))
    app.state.providers.drain_calendar("northline", value["booking_id"])
    assert app.state.service.appointment("northline", value["booking_id"])["status"] == "pending"
    jobs = app.state.service.snapshot("northline")["jobs"]
    assert len(jobs) == 1 and jobs[0]["status"] == "reconcile"
    app.state.worker.reconcile("northline", jobs[0]["id"])
    app.state.worker.run_one(jobs[0]["id"])
    assert app.state.service.appointment("northline", value["booking_id"])["status"] == "confirmed"
    assert len(app.state.service.snapshot("northline")["jobs"]) == 3


def test_cancel_and_reschedule_revision(app: FastAPI) -> None:
    key = confirmed(app)
    value = ChangeInput(
        operation_id="move",
        action="reschedule",
        start=request(app, hour=14).start,
        confirmed=True,
        expected_revision=1,
    )
    app.state.service.change("northline", key, value)
    app.state.providers.drain_calendar("northline", key)
    moved = app.state.service.appointment("northline", key)
    assert moved["revision"] == 2 and moved["status"] == "confirmed"
    with pytest.raises(DomainError, match="revision"):
        app.state.service.change(
            "northline", key, value.model_copy(update={"operation_id": "stale"})
        )
    cancel = ChangeInput(
        operation_id="cancel", action="cancel", confirmed=True, expected_revision=2
    )
    app.state.service.change("northline", key, cancel)
    app.state.providers.drain_calendar("northline", key)
    assert app.state.service.appointment("northline", key)["status"] == "cancelled"


@pytest.mark.parametrize(
    "change,error",
    [
        ({"service": "Unknown"}, "unsupported_service"),
        ({"start": "2026-11-01T01:30:00-04:00"}, "ambiguous"),
        ({"start": "2026-11-02T10:00:00-04:00"}, "offset_mismatch"),
        ({"start": "2020-01-01T10:00:00-05:00"}, "outside_booking_window"),
        ({"start": "2026-10-09T18:00:00-04:00"}, "invalid_slot"),
    ],
)
def test_time_service_validation(app: FastAPI, change: dict[str, str], error: str) -> None:
    from datetime import datetime

    data = request(app).model_dump()
    data.update({k: datetime.fromisoformat(v) if k == "start" else v for k, v in change.items()})
    with pytest.raises(DomainError, match=error):
        app.state.service.book("northline", BookingInput.model_validate(data))


def test_tenant_booking_isolation(app: FastAPI) -> None:
    app.state.service.seed("other")
    key = confirmed(app)
    with pytest.raises(DomainError, match="not_found"):
        app.state.service.appointment("other", key)
    assert app.state.service.snapshot("other")["appointments"] == []


def test_lease_owner_fencing_and_recovery(app: FastAPI) -> None:
    value = app.state.service.book("northline", request(app))
    key, token = app.state.worker.claim()
    assert app.state.worker.claim() is None
    with app.state.service.sessions.begin() as session:
        job = session.get(Job, key)
        job.lease_until = now() - timedelta(seconds=1)
    new_key, new_token = app.state.worker.claim()
    assert key == new_key and token != new_token
    app.state.worker.finish(key, token, "completed", "old_owner", None)
    with app.state.service.sessions() as session:
        assert session.get(Job, key).lease_token == new_token
    app.state.worker.calendar("northline", value["booking_id"], new_token, key)
    app.state.worker.finish(key, new_token, "completed", "verified", key)
    assert app.state.service.appointment("northline", value["booking_id"])["status"] == "confirmed"


def test_expired_delivery_lease_is_unknown_not_retried(app: FastAPI) -> None:
    confirmed(app)
    with app.state.service.sessions.begin() as s:
        job = s.scalar(select(Job).where(Job.kind == "followup"))
        job.status, job.lease_token = "running", "fake-expired-owner"
        job.lease_until = now() - timedelta(seconds=1)
        key = job.id
    app.state.worker.claim()
    with app.state.service.sessions() as s:
        assert s.get(Job, key).status == "unknown"
    with pytest.raises(DomainError, match="reconciliation"):
        app.state.service.replay("northline", key)
