from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from voicebridge.contracts import DocumentInput, DomainError
from voicebridge.db import Job, Tenant

from .test_booking_engine import confirmed


def test_fact_conflict_checks_other_documents_without_query_words(app: FastAPI) -> None:
    service = app.state.service
    service.document(
        "northline",
        DocumentInput(name="Warranty", text="Warranty lasts thirty days", fact_key="warranty"),
    )
    service.document(
        "northline",
        DocumentInput(name="Guarantee", text="Guarantee lasts ninety days", fact_key="warranty"),
    )
    assert service.answer("northline", "warranty")["status"] == "abstained"


@pytest.mark.parametrize("value", [{}, [], None, 42, ""])
def test_invalid_booking_lookup_returns_mcp_tool_error(app: FastAPI, value: Any) -> None:
    with TestClient(app) as client:
        result = client.post(
            "/mcp/business",
            headers={
                "Authorization": "Bearer "
                + app.state.service.settings.business_key.get_secret_value()
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "get_booking", "arguments": {"booking_id": value}},
            },
        )
    assert result.status_code == 200
    assert result.json()["result"]["isError"] is True


def test_invalid_n8n_json_is_unknown_and_worker_continues(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    confirmed(app)
    app.state.service.settings.followup_transport = "n8n"
    transport = httpx.MockTransport(lambda request: httpx.Response(200, content=b"not-json"))
    client_class = httpx.Client
    monkeypatch.setattr(
        httpx, "Client", lambda **kwargs: client_class(transport=transport, **kwargs)
    )
    with app.state.service.sessions() as session:
        followup = session.scalar(select(Job).where(Job.kind == "followup"))
        crm = session.scalar(select(Job).where(Job.kind == "crm"))
        followup_id, crm_id = followup.id, crm.id
    assert app.state.worker.run_one(followup_id)
    with app.state.service.sessions() as session:
        assert session.get(Job, followup_id).status == "unknown"
    assert app.state.worker.run_one(crm_id)
    with app.state.service.sessions() as session:
        assert session.get(Job, crm_id).status == "completed"


@pytest.mark.parametrize("limit", ["count", "bytes"])
def test_invalid_seed_limits_do_not_create_tenant(app: FastAPI, limit: str) -> None:
    service = app.state.service
    if limit == "count":
        service.settings.max_documents = 1
    else:
        service.settings.max_document_bytes = 1
    with pytest.raises(DomainError, match="document_limit|document_too_large"):
        service.seed("test-rejected-seed")
    with service.sessions() as session:
        assert session.get(Tenant, "test-rejected-seed") is None
