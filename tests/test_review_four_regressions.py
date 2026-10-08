from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from voicebridge.contracts import ChangeInput
from voicebridge.db import Appointment, Record
from voicebridge.service import identity

from .test_booking_engine import request


@pytest.mark.parametrize("arguments", [None, [], 42])
def test_nonobject_mcp_change_preserves_protocol_response(app: FastAPI, arguments: Any) -> None:
    credential = app.state.service.settings.business_key.get_secret_value()
    with TestClient(app) as client:
        response = client.post(
            "/mcp/business",
            headers={"Authorization": "Bearer " + credential},
            json={
                "jsonrpc": "2.0",
                "id": "malformed-change",
                "method": "tools/call",
                "params": {"name": "change_booking", "arguments": arguments},
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == "malformed-change" and result["result"]["isError"] is True
        assert result["result"]["content"][0]["text"] == "invalid_tool_arguments"


def test_fixture_cleanup_pages_every_booking_before_completion(app: FastAPI) -> None:
    providers = app.state.providers
    fixture_id = identity()
    with app.state.service.sessions.begin() as session:
        session.add(
            Record(
                id=identity(),
                tenant_id="northline",
                kind="evaluation_fixture",
                key=fixture_id,
                value={"status": "pending", "booking_ids": [], "detail": "fixture_started"},
            )
        )
    runner = providers.fixture_provider("northline", fixture_id)
    tenant = runner.service.settings.tenant_id
    runner.service.seed(tenant)
    bookings = []
    for hour in [10, 14]:
        result = runner.service.book(tenant, request(app, "fixture-" + str(hour), hour))
        runner.drain_calendar(tenant, result["booking_id"])
        bookings.append(result["booking_id"])
    # Ensure the row returned by the old LIMIT1 implementation is cancelled,
    # while another accepted fixture booking still needs cleanup.
    with app.state.service.sessions() as session:
        first = session.scalar(select(Appointment).where(Appointment.tenant_id == tenant).limit(1))
        first_id = first.id
    runner.service.change(
        tenant,
        first_id,
        ChangeInput(
            operation_id="fixture-first-cancel",
            action="cancel",
            confirmed=True,
            expected_revision=1,
        ),
    )
    runner.drain_calendar(tenant, first_id)
    app.state.service.settings = app.state.service.settings.model_copy(
        update={"max_records_per_page": 1}
    )
    result = providers.cleanup_fixture("northline", fixture_id)
    assert result["status"] == "completed"
    assert set(result["booking_ids"]) == set(bookings)
    for key in bookings:
        assert runner.service.appointment(tenant, key)["status"] == "cancelled"
        assert runner.service.calendar.get(key)["status"] == "cancelled"
