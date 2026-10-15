"""Real HTTP/PostgreSQL audit regressions; all credentials and payloads are fake."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from voicebridge import service as service_module
from voicebridge.db import Audit, Record, tenant_lock


def call(name: str, arguments: object = None) -> dict[str, object]:
    return {
        "jsonrpc": "2.0",
        "id": "test-private-request-id",
        "method": "tools/call",
        "params": {"name": name, "arguments": {} if arguments is None else arguments},
    }


def headers(app: FastAPI, key: str) -> dict[str, str]:
    return {
        "Authorization": "Bearer " + getattr(app.state.service.settings, key).get_secret_value()
    }


def audits(app: FastAPI) -> list[tuple[str, str]]:
    with app.state.service.sessions() as session:
        return [
            (row.action, row.target)
            for row in session.scalars(select(Audit).where(Audit.action.like("mcp.%")))
        ]


@pytest.mark.parametrize("credential", ["", "Bearer test-private-invalid-key"])
def test_missing_or_wrong_credentials_are_audited(app: FastAPI, credential: str) -> None:
    with TestClient(app) as client:
        response = client.post(
            "/mcp/management", headers={"Authorization": credential}, json=call("get_state")
        )
    assert response.status_code == 401
    assert audits(app) == [("mcp.denied.authorization", "management:unauthorized:unknown")]


def test_cross_surface_credential_is_denied_and_audited(app: FastAPI) -> None:
    with TestClient(app) as client:
        response = client.post(
            "/mcp/management", headers=headers(app, "business_key"), json=call("get_state")
        )
    assert response.status_code == 401
    assert audits(app) == [("mcp.denied.authorization", "management:unauthorized:unknown")]


@pytest.mark.parametrize(
    ("surface", "key", "name", "arguments", "reason", "tool"),
    [
        ("business", "business_read_key", "create_booking", {}, "scope", "create_booking"),
        ("management", "management_read_key", "save_agent_draft", {}, "scope", "save_agent_draft"),
        ("business", "business_key", "get_state", {}, "scope", "get_state"),
        ("management", "management_key", "read_secret-test-private-token", {}, "scope", "unknown"),
        (
            "management",
            "management_key",
            "promote_agent",
            {"spend": True},
            "policy",
            "promote_agent",
        ),
        (
            "business",
            "business_key",
            "answer_question",
            {"query": "hours", "tenant_id": "test-foreign-private-tenant"},
            "arguments",
            "answer_question",
        ),
        (
            "business",
            "business_key",
            "answer_question",
            {"query": "test-private-argument", "api_key": "test-private-argument-key"},
            "arguments",
            "answer_question",
        ),
        (
            "business",
            "business_key",
            "answer_question",
            ["test-private-list"],
            "arguments",
            "answer_question",
        ),
    ],
)
def test_tool_denials_are_sanitized_and_do_not_mutate(
    app: FastAPI, surface: str, key: str, name: str, arguments: object, reason: str, tool: str
) -> None:
    before = app.state.service.snapshot(app.state.service.settings.tenant_id)
    with TestClient(app) as client:
        response = client.post(
            "/mcp/" + surface, headers=headers(app, key), json=call(name, arguments)
        )
    assert response.status_code == 200
    body = response.json()
    assert "error" in body or body["result"]["isError"]
    capability = "read" if "read_key" in key else "write"
    assert audits(app) == [("mcp.denied." + reason, f"{surface}:{capability}:{tool}")]
    after = app.state.service.snapshot(app.state.service.settings.tenant_id)
    for collection in ("appointments", "contacts", "calls", "jobs", "agent"):
        assert after[collection] == before[collection]
    with app.state.service.sessions() as session:
        rows = session.scalars(select(Record).where(Record.kind == "mcp_denial_limit"))
        saved = json.dumps([(row.key, row.value) for row in rows]) + json.dumps(audits(app))
    assert "test-private" not in saved and "test-foreign" not in saved


def test_allowed_read_does_not_write_denial(app: FastAPI) -> None:
    with TestClient(app) as client:
        response = client.post(
            "/mcp/management",
            headers=headers(app, "management_read_key"),
            json=call("get_agent_draft"),
        )
    assert response.json()["result"]["isError"] is False
    assert audits(app) == []


def test_concurrent_overflow_is_bounded_and_separate_from_authenticated_bucket(
    app: FastAPI,
) -> None:
    service = app.state.service
    service.settings = service.settings.model_copy(update={"mcp_denial_audit_limit_per_minute": 2})
    with TestClient(app) as client:

        def denied(_: int) -> int:
            return client.post("/mcp/management", json=call("get_state")).status_code

        with ThreadPoolExecutor(max_workers=5) as pool:
            assert list(pool.map(denied, range(7))) == [401] * 7
        client.post(
            "/mcp/management",
            headers=headers(app, "management_read_key"),
            json=call("promote_agent"),
        )
    result = audits(app)
    assert result.count(("mcp.denied.authorization", "management:unauthorized:unknown")) == 2
    assert result.count(("mcp.denials.suppressed", "management:unauthorized")) == 1
    assert ("mcp.denied.scope", "management:read:promote_agent") in result
    with service.sessions() as session:
        row = session.scalar(
            select(Record).where(
                Record.kind == "mcp_denial_limit", Record.key == "management:unauthorized"
            )
        )
        assert row and row.value["count"] == 7 and row.value["suppressed"] == 5
        assert row.value["total_count"] == 7 and row.value["total_suppressed"] == 5


def test_minute_rollover_preserves_cumulative_denial_counts(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = app.state.service
    service.settings = service.settings.model_copy(update={"mcp_denial_audit_limit_per_minute": 1})
    first = datetime(2026, 1, 1, tzinfo=UTC)
    monkeypatch.setattr(service_module, "now", lambda: first)
    with TestClient(app) as client:
        for _ in range(2):
            assert client.post("/mcp/management", json=call("get_state")).status_code == 401
        monkeypatch.setattr(service_module, "now", lambda: first + timedelta(minutes=1))
        for _ in range(2):
            assert client.post("/mcp/management", json=call("get_state")).status_code == 401
    assert len(audits(app)) == 4
    with service.sessions() as session:
        row = session.scalar(
            select(Record).where(
                Record.kind == "mcp_denial_limit", Record.key == "management:unauthorized"
            )
        )
        assert row and row.value["count"] == 2 and row.value["suppressed"] == 1
        assert row.value["total_count"] == 4 and row.value["total_suppressed"] == 2


def test_audit_failure_returns_sanitized_unavailable_without_tool_execution(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    def failed_audit(*_: object) -> None:
        raise SQLAlchemyError("test-private-database-detail")

    def forbidden_invoke(*_: object, **__: object) -> None:
        pytest.fail("Denied request must never execute a tool")

    monkeypatch.setattr(app.state.service, "mcp_denied", failed_audit)
    monkeypatch.setattr(app.state.providers, "invoke", forbidden_invoke)
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/mcp/management", json=call("get_state"))
        assert response.status_code == 503 and response.json() == {"error": "audit_unavailable"}
        scoped = client.post(
            "/mcp/management",
            headers=headers(app, "management_read_key"),
            json=call("promote_agent"),
        )
        assert scoped.status_code == 503 and scoped.json() == {"error": "audit_unavailable"}


def test_denial_lock_does_not_wait_for_business_tenant_lock(app: FastAPI) -> None:
    service = app.state.service
    with ThreadPoolExecutor(max_workers=1) as pool:
        with service.sessions.begin() as session:
            tenant_lock(session, service.settings.tenant_id)
            future = pool.submit(
                service.mcp_denied, "management", "unauthorized", None, "authorization"
            )
            future.result(timeout=5)
    assert audits(app) == [("mcp.denied.authorization", "management:unauthorized:unknown")]
