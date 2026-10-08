from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from voicebridge.connectors import LocalCalendar, RetryableFailure, UnknownOutcome
from voicebridge.contracts import BookingInput
from voicebridge.db import Appointment, ExternalRecord

from .test_http_providers_knowledge import headers


def test_evaluation_calendar_cannot_collide_with_concurrent_business_booking(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    put = LocalCalendar.put
    business_created = False

    def interleaved(calendar: LocalCalendar, key: str, payload: dict[str, Any]) -> str:
        nonlocal business_created
        if not business_created:
            business_created = True
            service = app.state.service
            booking = service.book(
                "northline",
                BookingInput(
                    **service.evaluations.contact,
                    operation_id="test-concurrent-business",
                    service=payload["service"],
                    start=datetime.fromisoformat(payload["start"]).astimezone(
                        ZoneInfo(service.business.timezone)
                    ),
                    confirmed=True,
                ),
            )
            app.state.providers.drain_calendar("northline", booking["booking_id"])
        result = put(calendar, key, payload)
        with app.state.service.sessions() as session:
            business_events = session.scalars(
                select(ExternalRecord).where(ExternalRecord.kind == "calendar")
            )
            assert sum(event.value["status"] != "cancelled" for event in business_events) == 1
        return result

    monkeypatch.setattr(LocalCalendar, "put", interleaved)
    result = app.state.providers.evaluate("northline")
    assert all(case["passed"] for case in result["cases"])
    assert len(app.state.service.snapshot("northline")["appointments"]) == 1


def test_ambiguous_evaluation_write_is_cancelled_and_cleanup_receipt_verified(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    put = LocalCalendar.put

    def uncertain(calendar: LocalCalendar, key: str, payload: dict[str, Any]) -> str:
        put(calendar, key, payload)
        raise UnknownOutcome("test-simulator-write-after-timeout")

    monkeypatch.setattr(LocalCalendar, "put", uncertain)
    result = app.state.providers.evaluate("northline")
    positive = next(case for case in result["cases"] if case["kind"] == "booking")
    assert positive["passed"] is False
    fixtures = app.state.service.snapshot("northline")["evaluation_fixtures"]
    assert len(fixtures) == 1 and fixtures[0]["status"] == "completed"
    with app.state.service.sessions() as session:
        bookings = session.scalars(select(Appointment))
        assert all(booking.status == "cancelled" for booking in bookings)


def test_failed_fixture_cleanup_is_visible_owned_and_recoverable(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    put = LocalCalendar.put

    def unavailable(*args: object, **kwargs: object) -> str:
        raise RetryableFailure("test-calendar-unavailable-before-send")

    monkeypatch.setattr(LocalCalendar, "put", unavailable)
    app.state.providers.evaluate("northline")
    fixtures = app.state.service.snapshot("northline")["evaluation_fixtures"]
    assert len(fixtures) == 1 and fixtures[0]["status"] == "pending"
    fixture_id = fixtures[0]["id"]
    # The normal business worker cannot dispatch fixture jobs into its calendar.
    assert app.state.worker.claim() is None
    monkeypatch.setattr(LocalCalendar, "put", put)
    with TestClient(app) as client:
        path = "/api/evaluations/" + fixture_id + "/cleanup"
        assert client.post(path).status_code == 401
        response = client.post(path, headers=headers(app))
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
