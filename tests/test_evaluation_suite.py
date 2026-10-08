from fastapi import FastAPI
from fastapi.testclient import TestClient

from .test_http_providers_knowledge import headers


def test_evaluation_skips_existing_calendar_booking(app: FastAPI) -> None:
    from datetime import timedelta
    from zoneinfo import ZoneInfo

    from voicebridge.contracts import BookingInput
    from voicebridge.db import now

    service = app.state.service
    start = (now() + timedelta(days=1)).astimezone(ZoneInfo(service.business.timezone))
    start = start.replace(hour=service.business.opening_hour, minute=0, second=0, microsecond=0)
    while start.weekday() not in service.business.weekdays:
        start += timedelta(days=1)
    booked = service.book(
        "northline",
        BookingInput(
            **service.evaluations.contact,
            operation_id="test-existing-evaluation-slot",
            service=next(iter(service.business.services)),
            start=start,
            confirmed=True,
        ),
    )
    app.state.providers.drain_calendar("northline", booked["booking_id"])
    before = service.snapshot("northline")["appointments"]
    result = app.state.providers.evaluate("northline")
    assert all(case["passed"] for case in result["cases"]), result["cases"]
    assert service.snapshot("northline")["appointments"] == before


def test_versioned_evaluations_exercise_business_and_both_adapters(app: FastAPI) -> None:
    with TestClient(app) as c:
        before = app.state.service.snapshot("northline")["appointments"]
        response = c.post("/api/evaluations", headers=headers(app))
        assert response.status_code == 200
        result = response.json()
        assert result["revision"] == 3
        assert {case["id"] for case in result["cases"]} == {
            "hours",
            "unsupported-price",
            "injection",
            "explicit-confirmation",
            "timezone-required",
            "tenant-isolation",
            "retell-vapi-parity",
            "successful-booking-both-adapters",
            "retrieved-instruction-is-data",
        }
        assert all(case["passed"] for case in result["cases"]), result["cases"]
        snapshot = app.state.service.snapshot("northline")
        assert snapshot["appointments"] == before
        assert {call["provider"] for call in snapshot["calls"]} == {"retell", "vapi"}
        assert all(call["state"] == "ended" for call in snapshot["calls"])
        assert result["acoustic"] == "not_tested"


def test_versioned_evaluation_detects_broken_successful_booking(app: FastAPI, monkeypatch) -> None:
    from voicebridge.contracts import DomainError

    def reject(*args, **kwargs):
        raise DomainError("explicit_confirmation_required", 422)

    monkeypatch.setattr(type(app.state.service), "book", reject)
    result = app.state.providers.evaluate("northline")
    positive = next(c for c in result["cases"] if c["id"] == "successful-booking-both-adapters")
    assert positive["passed"] is False
