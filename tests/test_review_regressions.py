import json
from datetime import timedelta

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from voicebridge.connectors import GoogleCalendar, UnknownOutcome
from voicebridge.contracts import ChangeInput, DocumentInput, DomainError
from voicebridge.db import Job, now

from .test_booking_engine import request


def test_unfinished_create_replay_cannot_undo_cancel(app: FastAPI) -> None:
    value = app.state.service.book("northline", request(app))
    key, token = app.state.worker.claim()
    app.state.worker.calendar("northline", value["booking_id"], token, key)
    app.state.service.change(
        "northline",
        value["booking_id"],
        ChangeInput(operation_id="cancel", action="cancel", confirmed=True, expected_revision=1),
    )
    app.state.providers.drain_calendar("northline", value["booking_id"])
    with app.state.service.sessions.begin() as s:
        job = s.get(Job, key)
        job.lease_until = now() - timedelta(seconds=1)
    app.state.worker.run_one(key)
    assert app.state.service.appointment("northline", value["booking_id"])["status"] == "cancelled"
    assert app.state.service.calendar.get(value["booking_id"])["status"] == "cancelled"
    with app.state.service.sessions() as s:
        assert s.get(Job, key).status == "superseded"


def test_expired_owner_cannot_write_calendar_or_complete(app: FastAPI) -> None:
    value = app.state.service.book("northline", request(app))
    key, token = app.state.worker.claim()
    with app.state.service.sessions.begin() as s:
        s.get(Job, key).lease_until = now() - timedelta(seconds=1)
    with pytest.raises(UnknownOutcome, match="lease"):
        app.state.worker.calendar("northline", value["booking_id"], token, key)
    assert app.state.service.calendar.get(value["booking_id"]) is None
    app.state.worker.finish(key, token, "completed", "expired_owner", key)
    with app.state.service.sessions() as s:
        assert s.get(Job, key).status == "running"


def test_remote_write_404_is_not_a_receipt(app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = app.state.service.settings
    settings = settings.model_copy(
        update={"provider": settings.provider.model_copy(update={"enabled": True})}
    )
    calendar = GoogleCalendar(settings)
    monkeypatch.setattr(calendar, "headers", lambda: {"Authorization": "Bearer test-key"})

    def absent(self: httpx.Client, method: str, url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(404, json={"error": "missing"}, request=httpx.Request(method, url))

    monkeypatch.setattr(httpx.Client, "request", absent)
    value = request(app)
    with pytest.raises(DomainError, match="connector"):
        calendar.put(
            "testbooking",
            {
                "start": value.start.isoformat(),
                "end": value.start.isoformat(),
                "status": "confirmed",
                "service": value.service,
                "revision": 1,
            },
        )


def test_conflict_detection_is_independent_of_passage_limit(app: FastAPI) -> None:
    app.state.service.settings.search_limit = 1
    for duration in ["thirty", "ninety"]:
        app.state.service.document(
            "northline",
            DocumentInput(
                name="Warranty", text="Warranty lasts " + duration + " days.", fact_key="warranty"
            ),
        )
    assert app.state.service.answer("northline", "warranty")["status"] == "abstained"


def test_mcp_tool_errors_preserve_rpc_identity(app: FastAPI) -> None:
    headers = {
        "Authorization": "Bearer " + app.state.service.settings.business_key.get_secret_value()
    }
    with TestClient(app) as c:
        r = c.post(
            "/mcp/business",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": "test-rpc",
                "method": "tools/call",
                "params": {"name": "answer_question", "arguments": {"query": ""}},
            },
        )
        assert r.status_code == 200
        assert r.json()["id"] == "test-rpc" and r.json()["result"]["isError"] is True


def test_vapi_invalid_tool_does_not_abort_valid_batch(app: FastAPI) -> None:
    registered = app.state.providers.register("northline", "vapi", "test-call", "test-agent")
    value = request(app)
    body = {
        "message": {
            "type": "tool-calls",
            "call": {"id": "test-call", "assistantId": "test-agent"},
            "toolCallList": [
                {
                    "id": "bad",
                    "function": {"name": "create_booking", "arguments": {"confirmed": False}},
                },
                {
                    "id": "good",
                    "function": {
                        "name": "check_availability",
                        "arguments": {"start": value.start.isoformat(), "service": value.service},
                    },
                },
            ],
        }
    }
    result = app.state.providers.tools("vapi", body, registered["capability"])
    assert result["results"][0]["error"] == "invalid_tool_arguments"
    assert json.loads(result["results"][1]["result"])["available"] is True


@pytest.mark.parametrize(
    "method,params,code",
    [
        ("tools/call", {"name": "save_agent_draft"}, -32602),
        ("tools/call", [], -32602),
        ("initialize", {}, -32602),
        ("unknown", {}, -32601),
    ],
)
def test_mcp_protocol_errors_keep_identity(
    app: FastAPI, method: str, params: object, code: int
) -> None:
    with TestClient(app) as c:
        response = c.post(
            "/mcp/business",
            headers={"Authorization": "Bearer test-business-credential-local-only"},
            json={"jsonrpc": "2.0", "id": 7, "method": method, "params": params},
        )
        assert response.status_code == 200
        assert response.json()["id"] == 7
        assert response.json()["error"]["code"] == code
