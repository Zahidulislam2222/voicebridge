from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import timedelta
from threading import Event

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from voicebridge.contracts import BookingInput, ChangeInput, DocumentInput, DomainError
from voicebridge.db import Job, now

from .test_booking_engine import request
from .test_http_providers_knowledge import headers


@pytest.mark.parametrize("kind", ["crm", "followup"])
def test_stale_delivery_claim_never_dispatches(
    app: FastAPI, kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    booking = app.state.service.book("northline", request(app))
    app.state.providers.drain_calendar("northline", booking["booking_id"])
    with app.state.service.sessions() as s:
        from sqlalchemy import select

        job_id = s.scalar(select(Job.id).where(Job.kind == kind))
    claim = app.state.worker.claim(job_id)
    original = app.state.worker.claim

    def reclaimed(_: str | None = None) -> tuple[str, str]:
        with app.state.service.sessions.begin() as s:
            row = s.get(Job, job_id)
            row.lease_until = now() - timedelta(seconds=1)
        original("no-such-job")
        return claim

    effects = []
    monkeypatch.setattr(app.state.worker, "claim", reclaimed)
    monkeypatch.setattr(app.state.worker.delivery, kind, lambda *a, **kw: effects.append(a))
    app.state.worker.run_one(job_id)
    assert effects == []
    with app.state.service.sessions() as s:
        assert s.get(Job, job_id).status == "unknown"


def test_recipient_list_rejected_at_booking_and_delivery(app: FastAPI) -> None:
    malformed = "first@recipient.example,second.invalid"
    data = request(app).model_dump()
    with pytest.raises(ValidationError):
        BookingInput.model_validate({**data, "email": malformed})
    with pytest.raises(DomainError, match="synthetic_recipient"):
        app.state.worker.delivery.followup("test-operation", {"email": malformed})


def test_delivery_and_cancellation_have_a_serial_order(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sqlalchemy import select

    booking = app.state.service.book("northline", request(app))
    app.state.providers.drain_calendar("northline", booking["booking_id"])
    with app.state.service.sessions() as s:
        job_id = s.scalar(select(Job.id).where(Job.kind == "followup"))
    dispatched, release = Event(), Event()
    events = []

    def send(*args: object) -> str:
        dispatched.set()
        assert release.wait(5)
        events.append("sent")
        return "test-receipt"

    def cancel() -> None:
        app.state.service.change(
            "northline",
            booking["booking_id"],
            ChangeInput(
                operation_id="cancel-during-delivery",
                action="cancel",
                confirmed=True,
                expected_revision=1,
            ),
        )
        events.append("cancelled")

    monkeypatch.setattr(app.state.worker.delivery, "followup", send)
    with ThreadPoolExecutor(max_workers=2) as pool:
        sending = pool.submit(app.state.worker.run_one, job_id)
        assert dispatched.wait(5)
        cancelling = pool.submit(cancel)
        try:
            with pytest.raises(TimeoutError):
                cancelling.result(timeout=0.1)
        finally:
            release.set()
        sending.result(timeout=5)
        cancelling.result(timeout=5)
    assert events == ["sent", "cancelled"]


@pytest.mark.parametrize("query", [None, 1, {}, True])
def test_malformed_knowledge_tool_is_readable_error(app: FastAPI, query: object) -> None:
    with TestClient(app) as c:
        result = c.post(
            "/mcp/business",
            headers={"Authorization": "Bearer test-business-credential-local-only"},
            json={
                "jsonrpc": "2.0",
                "id": "invalid-query",
                "method": "tools/call",
                "params": {"name": "answer_question", "arguments": {"query": query}},
            },
        )
        assert result.status_code == 200
        assert result.json()["id"] == "invalid-query"
        assert result.json()["result"]["isError"] is True
        assert (
            c.post(
                "/api/tools",
                headers=headers(app),
                json={"name": "answer_question", "arguments": {"query": query}},
            ).status_code
            == 422
        )


@pytest.mark.parametrize("key", ["retell_webhook_key", "vapi_webhook_key", "n8n_key"])
def test_empty_required_secret_rejected(app: FastAPI, key: str) -> None:
    settings = app.state.service.settings
    values = settings.model_dump()
    values[key] = ""
    with pytest.raises(ValidationError):
        type(settings).model_validate(values)


@pytest.mark.parametrize(
    "surface,key,read_tool,write_tool",
    [
        (
            "business",
            "test-business-read-credential-local-only",
            "answer_question",
            "create_booking",
        ),
        (
            "management",
            "test-management-read-credential-local-only",
            "get_agent_draft",
            "save_agent_draft",
        ),
    ],
)
def test_mcp_read_only_credentials_cannot_write(
    app: FastAPI, surface: str, key: str, read_tool: str, write_tool: str
) -> None:
    with TestClient(app) as c:
        headers = {"Authorization": "Bearer " + key}
        listed = c.post(
            "/mcp/" + surface,
            headers=headers,
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        )
        assert listed.status_code == 200
        names = {tool["name"] for tool in listed.json()["result"]["tools"]}
        assert read_tool in names and write_tool not in names
        denied = c.post(
            "/mcp/" + surface,
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": write_tool, "arguments": {}},
            },
        )
        assert denied.status_code == 200 and denied.json()["id"] == 2
        assert denied.json()["error"]["code"] == -32602


def test_reactivating_deleted_document_respects_limit(app: FastAPI) -> None:
    service = app.state.service
    rows = service.documents("northline")
    service.settings.max_documents = len(rows)
    service.delete_document("northline", rows[0]["id"])
    service.document("northline", DocumentInput(name="Replacement", text="Approved repair."))
    with pytest.raises(DomainError, match="document_limit"):
        service.document(
            "northline",
            DocumentInput(
                name="Reactivated",
                text="Approved repair.",
                expected_revision=rows[0]["revision"] + 1,
            ),
            rows[0]["id"],
        )
