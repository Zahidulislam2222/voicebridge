"""Bound call recovery requires an exact authenticated terminal provider receipt."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from voicebridge.connectors import RemoteTransport
from voicebridge.contracts import DomainError, NativeCallInput
from voicebridge.db import Audit, Call, Operation

from .test_native_calls import prepared_native
from .test_oidc_sessions import configured, login
from .test_oidc_sessions import issuer as issuer


def bound(app: FastAPI, tmp_path: Path) -> tuple[Any, str, NativeCallInput, dict[str, Any]]:
    native, _ = prepared_native(app, tmp_path)
    native.settings = native.settings.model_copy(update={"native_reconciliation_enabled": True})
    native.reconciliation_transport.settings = native.settings
    tenant = app.state.service.settings.tenant_id
    value = NativeCallInput(provider="retell", operation_id="test-reconcile-0001")
    grant = native.create(tenant, "test-owner", value)
    receipt = {
        "call_id": grant["callId"],
        "agent_id": "test-retell-agent",
        "metadata": {"voicebridge_operation": value.operation_id},
        "call_status": "error",
        "transcript": "Private words must not be copied by status reconciliation",
        "access_token": "test-private-grant",
    }
    return native, tenant, value, receipt


def test_terminal_receipt_releases_slot_once_without_copying_artifacts(
    app: FastAPI, tmp_path: Path
) -> None:
    native, tenant, value, receipt = bound(app, tmp_path)
    requests = []

    def read(method: str, url: str, *_: Any) -> dict[str, Any]:
        requests.append((method, url))
        assert method == "GET"
        assert url.endswith("/v2/get-call/test-native-call-1")
        return receipt

    native.reconciliation_transport.request = read
    result = native.reconcile(tenant, "test-owner", value)
    assert result["operations"][0]["state"] == "DONE"
    assert "Private words" not in str(result) and "test-private-grant" not in str(result)
    assert native.reconcile(tenant, "test-owner", value) == result
    assert len(requests) == 1
    with app.state.service.sessions() as session:
        row = session.scalar(select(Operation).where(Operation.key.endswith(value.operation_id)))
        assert row is not None and row.result["state"] == "DONE" and row.result["grant"] is None
        call = session.get(Call, row.result["intent_id"])
        assert call is not None and call.state == "ended" and call.transcript == []
        assert (
            len(
                list(session.scalars(select(Audit).where(Audit.action == "native.call.reconciled")))
            )
            == 1
        )


@pytest.mark.parametrize(
    "change",
    [
        {"call_id": "test-different-call"},
        {"agent_id": "test-other-agent"},
        {"metadata": {}},
        {"metadata": {"voicebridge_operation": "test-other-operation"}},
        {"call_status": "registered"},
        {"call_status": "ongoing"},
        {"call_status": "not_connected"},
        {"call_status": None},
    ],
)
def test_unverified_receipt_never_releases_bound_slot(
    app: FastAPI, tmp_path: Path, change: dict[str, Any]
) -> None:
    native, tenant, value, receipt = bound(app, tmp_path)
    native.reconciliation_transport.request = lambda *_: {**receipt, **change}
    with pytest.raises(DomainError):
        native.reconcile(tenant, "test-owner", value)
    assert native.status(tenant, "test-owner")["operations"][0]["state"] == "BOUND"


def test_other_owner_tenant_unknown_and_transport_failure_remain_closed(
    app: FastAPI, tmp_path: Path
) -> None:
    native, tenant, value, _ = bound(app, tmp_path)

    def unavailable(*_: Any) -> dict[str, Any]:
        raise TimeoutError("test provider unavailable")

    native.reconciliation_transport.request = unavailable
    for selected_tenant, owner in [(tenant, "other-owner"), ("other-tenant", "test-owner")]:
        with pytest.raises(DomainError) as denied:
            native.reconcile(selected_tenant, owner, value)
        assert denied.value.status == 404
    with pytest.raises(DomainError) as failed:
        native.reconcile(tenant, "test-owner", value)
    assert failed.value.code == "native_reconciliation_unverified"
    with app.state.service.sessions.begin() as session:
        row = session.scalar(select(Operation).where(Operation.key.endswith(value.operation_id)))
        assert row is not None
        row.result = {**row.result, "state": "UNKNOWN", "external_id": None}
    with pytest.raises(DomainError) as unknown:
        native.reconcile(tenant, "test-owner", value)
    assert unknown.value.code == "native_operation_requires_reconciliation"


def test_http_reconciliation_requires_owner_session_and_csrf(
    app: FastAPI, issuer: dict[str, Any], tmp_path: Path
) -> None:
    instance = configured(app, issuer, tmp_path)
    path = "/api/calls/native/reconcile"
    value = {"provider": "retell", "operation_id": "test-reconcile-0001"}
    with TestClient(instance) as client:
        assert client.post(path, json=value).status_code == 401
        assert login(client, issuer).status_code == 303
        assert client.post(path, json=value).status_code == 403
        csrf = client.get("/auth/session").json()["csrf"]
        headers = {"Origin": "http://localhost:18080", "X-CSRF-Token": csrf}
        assert client.post(path, json=value, headers=headers).status_code == 404
        native, _, _, receipt = bound(instance, tmp_path)
        native.reconciliation_transport.request = lambda *_: receipt
        result = client.post(path, json=value, headers=headers)
        assert result.status_code == 200
        assert result.json()["operations"][0]["state"] == "DONE"
    issuer.update(subject="test-operator", email="operator@example.invalid")
    with TestClient(instance) as client:
        assert login(client, issuer).status_code == 303
        csrf = client.get("/auth/session").json()["csrf"]
        assert (
            client.post(
                path,
                json=value,
                headers={
                    "Origin": "http://localhost:18080",
                    "X-CSRF-Token": csrf,
                },
            ).status_code
            == 403
        )


def test_vapi_uses_exact_call_get_and_only_ended_is_terminal(app: FastAPI, tmp_path: Path) -> None:
    native, tenant, value, _ = bound(app, tmp_path)
    value = value.model_copy(update={"provider": "vapi"})
    with app.state.service.sessions.begin() as session:
        row = session.scalar(select(Operation).where(Operation.key.endswith(value.operation_id)))
        assert row is not None
        row.key = "native:vapi:" + value.operation_id
        row.result = {**row.result, "provider": "vapi"}
        call = session.get(Call, row.result["intent_id"])
        assert call is not None
        call.provider, call.agent_id = "vapi", "test-vapi-agent"
    receipt = {
        "id": "test-native-call-1",
        "assistantId": "test-vapi-agent",
        "status": "in-progress",
        "assistantOverrides": {"metadata": {"voicebridge_operation": value.operation_id}},
    }

    def read(method: str, url: str, *_: Any) -> dict[str, Any]:
        assert method == "GET" and url.endswith("/call/test-native-call-1")
        return receipt

    native.reconciliation_transport.request = read
    with pytest.raises(DomainError):
        native.reconcile(tenant, "test-owner", value)
    receipt["status"] = "ended"
    good = receipt["assistantOverrides"]
    for malformed in [
        None,
        [],
        {},
        {"metadata": []},
        {"metadata": {}},
        {"metadata": {"voicebridge_operation": "test-wrong-operation"}},
    ]:
        receipt["assistantOverrides"] = malformed
        with pytest.raises(DomainError):
            native.reconcile(tenant, "test-owner", value)
    receipt["assistantOverrides"] = good
    result = native.reconcile(tenant, "test-owner", value)
    assert result["operations"][0]["state"] == "DONE"


def test_lost_webhook_recovery_does_not_require_fresh_call_spending_receipt(
    app: FastAPI, tmp_path: Path
) -> None:
    native, tenant, value, receipt = bound(app, tmp_path)
    native.settings.native_entitlement_file.write_text("{}")
    native.reconciliation_transport.request = lambda *_: receipt
    assert native.reconcile(tenant, "test-owner", value)["operations"][0]["state"] == "DONE"


def test_disabled_creation_can_reconcile_through_real_read_only_transport(
    app: FastAPI, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import httpx

    native, tenant, value, receipt = bound(app, tmp_path)
    native.settings = native.settings.model_copy(
        update={
            "provider": native.settings.provider.model_copy(update={"voice_enabled": False}),
        }
    )
    native.reconciliation_transport.settings = native.settings
    original = httpx.Client
    seen = []

    def respond(request: httpx.Request) -> httpx.Response:
        seen.append(request.method)
        return httpx.Response(200, json=receipt)

    monkeypatch.setattr(
        httpx, "Client", lambda **kwargs: original(**kwargs, transport=httpx.MockTransport(respond))
    )
    assert native.reconcile(tenant, "test-owner", value)["operations"][0]["state"] == "DONE"
    assert seen == ["GET"]
    for method in ["POST", "DELETE", "PUT", "PATCH"]:
        with pytest.raises(DomainError, match="external_execution_disabled"):
            native.reconciliation_transport.request(
                method, native.settings.provider.retell_base_url, {}
            )
    disabled = native.settings.model_copy(update={"native_reconciliation_enabled": False})
    with pytest.raises(DomainError, match="external_execution_disabled"):
        RemoteTransport(disabled, "voice_read").request(
            "GET", disabled.provider.retell_base_url, {}
        )
    with pytest.raises(DomainError, match="connector_destination_denied"):
        native.reconciliation_transport.request(
            "GET", "https://other.example.invalid/call/test", {}
        )
    with pytest.raises(DomainError, match="vapi_owner_resolution_required"):
        native.reconciliation_transport.request(
            "GET", native.settings.provider.vapi_base_url + "/call/test", {}
        )
    assert seen == ["GET"]


def test_parallel_reconciliations_record_one_terminal_transition(
    app: FastAPI, tmp_path: Path
) -> None:
    native, tenant, value, receipt = bound(app, tmp_path)
    ready = Barrier(2)

    def read(*_: Any) -> dict[str, Any]:
        ready.wait(timeout=10)
        return receipt

    native.reconciliation_transport.request = read
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: native.reconcile(tenant, "test-owner", value), range(2)))
    assert all(result["operations"][0]["state"] == "DONE" for result in results)
    with app.state.service.sessions() as session:
        assert (
            len(
                list(session.scalars(select(Audit).where(Audit.action == "native.call.reconciled")))
            )
            == 1
        )


@pytest.mark.parametrize("change", ["binding", "owner", "webhook"])
def test_provider_read_race_revalidates_binding_and_preserves_webhook_terminal(
    app: FastAPI, tmp_path: Path, change: str
) -> None:
    native, tenant, value, receipt = bound(app, tmp_path)

    def read(*_: Any) -> dict[str, Any]:
        with app.state.service.sessions.begin() as session:
            row = session.scalar(
                select(Operation).where(Operation.key.endswith(value.operation_id))
            )
            assert row is not None
            call = session.get(Call, row.result["intent_id"])
            assert call is not None
            if change == "binding":
                call.external_id = "test-other-binding"
            elif change == "owner":
                row.result = {**row.result, "owner": "test-other-owner"}
            else:
                call.state = "ended"
        return receipt

    native.reconciliation_transport.request = read
    if change == "webhook":
        assert native.reconcile(tenant, "test-owner", value)["operations"][0]["state"] == "DONE"
    else:
        with pytest.raises(DomainError):
            native.reconcile(tenant, "test-owner", value)
        with app.state.service.sessions() as session:
            row = session.scalar(
                select(Operation).where(Operation.key.endswith(value.operation_id))
            )
            assert row is not None and row.result["state"] == "BOUND"
