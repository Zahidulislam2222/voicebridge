"""Native call creation never joins media before a durable exact-ID bind."""

import json
from datetime import timedelta
from typing import Any
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import select
from voicebridge.contracts import DomainError, NativeCallInput
from voicebridge.db import Call, Operation, now


def prepared_native(app: FastAPI, tmp_path: Any) -> tuple[Any, list[dict[str, Any]]]:
    native = app.state.native_calls
    service = app.state.service
    service.profiles = service.profiles.model_copy(
        update={
            "retell": service.profiles.retell.model_copy(
                update={
                    "agent_id": "test-retell-agent",
                    "voice_id": "test-male-voice",
                    "version": 0,
                }
            )
        }
    )
    entitlement = tmp_path / "entitlement.json"
    entitlement.write_text(
        json.dumps(
            {
                "verified_at": now().isoformat(),
                "retell": {
                    "prepaid_balance_usd": 10,
                    "recharge_off": True,
                    "billable_addons_usd": 0,
                    "byok_count": 0,
                },
            }
        )
    )
    provider = service.settings.provider.model_copy(
        update={
            "voice_enabled": True,
            "retell_key": SecretStr("test-key" * 4),
            "retell_model": "test-model",
        }
    )
    approved_path = tmp_path / "retell-approved.json"
    approved = {
        "agent": {
            "agent_id": "test-retell-agent",
            "version": 0,
            "voice_id": "test-male-voice",
            "max_call_duration_ms": 60000,
            "response_engine": {"type": "retell-llm", "llm_id": "test-llm", "version": 0},
        },
        "llm": {"llm_id": "test-llm", "version": 0, "model": "test-model"},
    }
    approved_path.write_text(json.dumps(approved))
    settings = service.settings.model_copy(
        update={
            "stage": "pilot",
            "provider": provider,
            "provider_metadata_capability": True,
            "native_cipher_key": SecretStr(Fernet.generate_key().decode()),
            "native_entitlement_file": entitlement,
            "native_retell_approved_file": approved_path,
        }
    )
    native.settings = settings
    native.transport.settings = settings
    service.settings = settings
    seen: list[dict[str, Any]] = []

    def fake_request(
        method: str, url: str, headers: dict[str, str], payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if method == "GET":
            assert "?version=0" in url
            return approved["llm"] if "/get-retell-llm/" in url else approved["agent"]
        assert method == "POST"
        assert payload is not None
        seen.append(payload)
        return {
            "call_id": "test-native-call-1",
            "access_token": "test-media-grant-123456",
            "transport": "gateway",
            "ice_servers": [],
            "expires_at": int((now() + timedelta(seconds=60)).timestamp() * 1000),
        }

    native.transport.request = fake_request
    return native, seen


def test_native_exact_bind_and_idempotent_grant(app: FastAPI, tmp_path: Any) -> None:
    native, seen = prepared_native(app, tmp_path)
    tenant = app.state.service.settings.tenant_id
    value = NativeCallInput(provider="retell", operation_id="test-operation-0001")
    first = native.create(tenant, "test-owner", value)
    assert seen[0]["agent_version"] == 0
    second = native.create(tenant, "test-owner", value)
    assert first == second
    assert len(seen) == 1
    assert set(first) == {
        "provider",
        "callId",
        "accessToken",
        "transport",
        "iceServers",
        "expiresAt",
    }
    with app.state.service.sessions() as session:
        operation = session.scalar(
            select(Operation).where(Operation.key == "native:retell:" + value.operation_id)
        )
        assert operation is not None and operation.result["state"] == "BOUND"
        assert "test-media-grant-123456" not in json.dumps(operation.result)
        assert seen[0]["metadata"]["voicebridge_capability"] not in json.dumps(operation.result)
        call = session.get(Call, operation.result["intent_id"])
        assert call is not None and call.external_id == first["callId"]
    with pytest.raises(DomainError) as conflict:
        native.create(tenant, "different-owner", value)
    assert conflict.value.code == "native_operation_conflict"
    with pytest.raises(DomainError) as busy:
        native.create(
            tenant,
            "test-owner",
            NativeCallInput(provider="retell", operation_id="test-operation-0002"),
        )
    assert busy.value.code == "native_call_capacity_reached"
    app.state.service.seed("test-other-tenant")
    with pytest.raises(DomainError) as shared_account_busy:
        native.create(
            "test-other-tenant",
            "test-other-owner",
            NativeCallInput(provider="retell", operation_id="test-operation-0005"),
        )
    assert shared_account_busy.value.code == "native_call_capacity_reached"
    assert len(seen) == 1
    sessions = app.state.service.sessions
    opened = 0

    def one_checkout():
        nonlocal opened
        opened += 1
        if opened > 1:
            raise AssertionError("Native status must reuse its checked-out database session")
        return sessions()

    with patch.object(app.state.service, "sessions", one_checkout):
        status = native.status(tenant, "test-owner")
    assert opened == 1
    assert status["operations"][0]["recovery"] == "resume_existing_call"
    with app.state.service.sessions.begin() as session:
        operation = session.scalar(
            select(Operation).where(Operation.key == "native:retell:" + value.operation_id)
        )
        assert operation is not None
        operation.result = {
            **operation.result,
            "grant": native._seal({**first, "expiresAt": 1}),
        }
    expired = native.status(tenant, "test-owner")
    assert expired["operations"][0]["recovery"] == "manual_reconciliation_required"
    assert first["accessToken"] not in json.dumps(expired)
    with app.state.service.sessions.begin() as session:
        operation = session.scalar(
            select(Operation).where(Operation.key == "native:retell:" + value.operation_id)
        )
        assert operation is not None
        operation.result = {**operation.result, "grant": native._seal(first)}
        call = session.get(Call, operation.result["intent_id"])
        assert call is not None
        call.external_id = "test-mismatched-call"
    assert (
        native.status(tenant, "test-owner")["operations"][0]["recovery"]
        == "manual_reconciliation_required"
    )


def test_native_unknown_never_recreates(app: FastAPI, tmp_path: Any) -> None:
    native, _ = prepared_native(app, tmp_path)
    tenant = app.state.service.settings.tenant_id
    attempts = 0

    def ambiguous(*_: Any, **__: Any) -> dict[str, Any]:
        nonlocal attempts
        attempts += 1
        raise TimeoutError("test ambiguous transport")

    native._create_provider = ambiguous
    value = NativeCallInput(provider="retell", operation_id="test-operation-0003")
    with pytest.raises(DomainError) as first:
        native.create(tenant, "test-owner", value)
    assert first.value.code == "native_create_unverified"
    with pytest.raises(DomainError) as second:
        native.create(tenant, "test-owner", value)
    assert second.value.code == "native_operation_requires_reconciliation"
    assert attempts == 1
    with app.state.service.sessions() as session:
        operation = session.scalar(
            select(Operation).where(Operation.key == "native:retell:" + value.operation_id)
        )
        assert operation is not None and operation.result["state"] == "UNKNOWN"
    status = native.status(tenant, "test-owner")
    assert status["operations"] == [
        {
            "operation_id": value.operation_id,
            "provider": "retell",
            "state": "UNKNOWN",
            "created_at": operation.result["created_at"],
            "recovery": "manual_reconciliation_required",
        }
    ]
    assert status["limits"] == {"max_seconds": 60, "max_concurrent": 1}
    assert status["entitlements"]["retell"]["state"] == "verified"
    assert native.status(tenant, "different-owner")["operations"] == []
    assert "capability" not in json.dumps(status)
    assert "grant" not in json.dumps(status)


def test_native_status_requires_owner_session(app: FastAPI) -> None:
    with TestClient(app) as client:
        response = client.get(
            "/api/calls/native/status",
            headers={"Authorization": "Bearer test-operator-credential-local-only"},
        )
    assert response.status_code == 403
    assert response.json() == {"error": "native_owner_required"}


def test_retell_model_drift_blocks_creation(app: FastAPI, tmp_path: Any) -> None:
    native, seen = prepared_native(app, tmp_path)
    approved = json.loads(native.settings.native_retell_approved_file.read_text())

    def drifted_get(
        method: str, url: str, headers: dict[str, str], payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        assert method == "GET"
        if "/get-retell-llm/" in url:
            return {**approved["llm"], "model": "test-unapproved-model"}
        return approved["agent"]

    native.transport.request = drifted_get
    with pytest.raises(DomainError) as drift:
        native.create(
            native.settings.tenant_id,
            "test-owner",
            NativeCallInput(provider="retell", operation_id="test-drift-operation-001"),
        )
    assert drift.value.code == "native_profile_drift"
    assert seen == []


def test_native_disabled_and_unauthenticated_route(app: FastAPI) -> None:
    native = app.state.native_calls
    with pytest.raises(DomainError) as disabled:
        native.create(
            app.state.service.settings.tenant_id,
            "test-owner",
            NativeCallInput(provider="retell", operation_id="test-operation-0004"),
        )
    assert disabled.value.code == "external_execution_disabled"
    with TestClient(app) as client:
        response = client.post(
            "/api/calls/native/create",
            json={"provider": "retell", "operation_id": "test-operation-0004"},
        )
    assert response.status_code == 401


def test_vapi_each_server_receives_capability_and_browser_does_not(
    app: FastAPI, tmp_path: Any
) -> None:
    native, _ = prepared_native(app, tmp_path)
    service = app.state.service
    service.profiles = service.profiles.model_copy(
        update={
            "vapi": service.profiles.vapi.model_copy(
                update={
                    "agent_id": "test-vapi-assistant",
                    "voice_id": "test-vapi-voice",
                    "version": "v1",
                }
            )
        }
    )
    origin = service.settings.origins[0].rstrip("/")
    server = {
        "url": origin + "/engine-api/providers/vapi/events",
        "headers": {"Authorization": "Bearer test-webhook"},
    }
    tool_server = {
        "url": origin + "/engine-api/providers/vapi/tools",
        "headers": {"Authorization": "Bearer test-webhook"},
    }
    template = {
        "vapi-assistant": {
            "voice": {"provider": "vapi", "voiceId": "test-vapi-voice"},
            "maxDurationSeconds": 60,
            "artifactPlan": {
                "recordingEnabled": False,
                "loggingEnabled": False,
                "pcapEnabled": False,
                "transcriptPlan": {"enabled": True},
            },
            "firstMessage": "Hello, this is an owner-only test.",
            "serverMessages": ["tool-calls", "end-of-call-report"],
            "silenceTimeoutSeconds": 10,
            "transcriber": {"provider": "test-transcriber"},
            "server": server,
            "model": {
                "provider": "openai",
                "model": "test-model",
                "tools": [{"function": {"name": "answer_question"}, "server": tool_server}],
            },
        }
    }
    template_path = tmp_path / "native-template.json"
    template_path.write_text(json.dumps(template))
    entitlement = tmp_path / "entitlement.json"
    data = json.loads(entitlement.read_text())
    data["vapi"] = {
        "prepaid_balance_usd": 5,
        "recharge_off": True,
        "billable_addons_usd": 0,
        "byok_count": 0,
        "card_absent": True,
    }
    entitlement.write_text(json.dumps(data))
    provider = service.settings.provider.model_copy(
        update={
            "vapi_key": SecretStr("test-key" * 4),
            "vapi_owner_resolved": True,
            "vapi_model": "test-model",
        }
    )
    settings = service.settings.model_copy(
        update={
            "provider": provider,
            "vapi_webhook_key": SecretStr("test-webhook"),
            "native_template_file": template_path,
        }
    )
    service.settings = native.settings = native.transport.settings = settings
    seen: list[dict[str, Any]] = []

    def fake_request(
        method: str, url: str, headers: dict[str, str], payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if method == "GET":
            return {
                "id": "test-vapi-assistant",
                "latestVersion": "v1",
                "voice": template["vapi-assistant"]["voice"],
                "maxDurationSeconds": 60,
                "model": template["vapi-assistant"]["model"],
                "server": template["vapi-assistant"]["server"],
                "transcriber": template["vapi-assistant"]["transcriber"],
                "artifactPlan": template["vapi-assistant"]["artifactPlan"],
                "serverMessages": template["vapi-assistant"]["serverMessages"],
                "silenceTimeoutSeconds": 10,
            }
        assert payload is not None
        seen.append(payload)
        return {
            "id": "test-vapi-call-1",
            "webCallUrl": "https://test.daily.co/test-room",
            "transport": {"callToken": "test-call-token"},
        }

    native.transport.request = fake_request
    grant = native.create(
        settings.tenant_id,
        "test-owner",
        NativeCallInput(provider="vapi", operation_id="test-vapi-operation-0001"),
    )
    assert len(seen) == 1
    assert seen[0]["assistantVersion"] == "v1"
    assert seen[0]["assistantOverrides"]["artifactPlan"] == {
        "recordingEnabled": False,
        "loggingEnabled": False,
        "pcapEnabled": False,
        "transcriptPlan": {"enabled": True},
    }
    assert (
        seen[0]["assistantOverrides"]["firstMessage"] == template["vapi-assistant"]["firstMessage"]
    )
    assert set(grant) == {"provider", "callId", "webCallUrl", "callToken", "expiresAt"}
    assert "test-webhook" not in json.dumps(grant)
    assert "test-key" not in json.dumps(grant)
    event_headers = seen[0]["assistantOverrides"]["server"]["headers"]
    tool_headers = seen[0]["assistantOverrides"]["model"]["tools"][0]["server"]["headers"]
    assert event_headers["x-call-capability"] == tool_headers["x-call-capability"]
    assert event_headers["Authorization"] == "Bearer test-webhook"


def test_vapi_version_recording_or_extra_tool_drift_blocks_creation(
    app: FastAPI, tmp_path: Any
) -> None:
    native, _ = prepared_native(app, tmp_path)
    entitlement_path = native.settings.native_entitlement_file
    evidence = json.loads(entitlement_path.read_text())
    evidence["vapi"] = {
        "prepaid_balance_usd": 5,
        "recharge_off": True,
        "billable_addons_usd": 0,
        "byok_count": 0,
        "card_absent": True,
    }
    entitlement_path.write_text(json.dumps(evidence))
    profile = app.state.service.profiles.vapi.model_copy(
        update={"agent_id": "test-vapi-assistant", "voice_id": "test-vapi-voice", "version": "v1"}
    )
    app.state.service.profiles = app.state.service.profiles.model_copy(update={"vapi": profile})
    template = {
        "vapi-assistant": {
            "voice": {"provider": "vapi", "voiceId": "test-vapi-voice"},
            "model": {
                "provider": "openai",
                "model": "test-model",
                "tools": [
                    {
                        "function": {"name": "answer_question"},
                        "server": {
                            "url": native.settings.origins[0] + "/engine-api/providers/vapi/tools",
                            "headers": {"Authorization": "Bearer test-webhook"},
                        },
                    }
                ],
            },
            "server": {
                "url": native.settings.origins[0] + "/engine-api/providers/vapi/events",
                "headers": {"Authorization": "Bearer test-webhook"},
            },
            "firstMessage": "Owner-only test.",
            "artifactPlan": {
                "recordingEnabled": False,
                "loggingEnabled": False,
                "pcapEnabled": False,
                "transcriptPlan": {"enabled": True},
            },
            "transcriber": {"provider": "test-transcriber"},
            "serverMessages": ["tool-calls", "end-of-call-report"],
            "silenceTimeoutSeconds": 10,
            "maxDurationSeconds": 60,
        }
    }
    path = tmp_path / "vapi-template.json"
    path.write_text(json.dumps(template))
    provider = native.settings.provider.model_copy(update={"vapi_model": "test-model"})
    settings = native.settings.model_copy(
        update={
            "provider": provider,
            "native_template_file": path,
            "vapi_webhook_key": SecretStr("test-webhook"),
        }
    )
    native.settings = native.transport.settings = settings

    def drifted_get(
        method: str, url: str, headers: dict[str, str], payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        assert method == "GET"
        return {
            **template["vapi-assistant"],
            "id": profile.agent_id,
            "latestVersion": "v2",
            "artifactPlan": {"recordingEnabled": True},
        }

    native.transport.request = drifted_get
    with pytest.raises(DomainError) as drift:
        native.create(
            settings.tenant_id,
            "test-owner",
            NativeCallInput(provider="vapi", operation_id="test-drift-operation-002"),
        )
    assert drift.value.code == "native_profile_drift"

    def extra_tool_get(
        method: str, url: str, headers: dict[str, str], payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        assert method == "GET", "No call may be created after tool drift"
        return {
            **template["vapi-assistant"],
            "id": profile.agent_id,
            "latestVersion": "v1",
            "model": {**template["vapi-assistant"]["model"], "toolIds": ["unapproved-tool"]},
        }

    native.transport.request = extra_tool_get
    with pytest.raises(DomainError) as extra_tool:
        native.create(
            settings.tenant_id,
            "test-owner",
            NativeCallInput(provider="vapi", operation_id="test-drift-operation-003"),
        )
    assert extra_tool.value.code == "native_profile_drift"

    safe_artifacts = template["vapi-assistant"]["artifactPlan"]
    for unsafe_artifacts in (
        {"recordingEnabled": False},
        {**safe_artifacts, "loggingEnabled": True},
        {**safe_artifacts, "pcapEnabled": True},
        {**safe_artifacts, "transcriptPlan": {"enabled": False}},
    ):
        template["vapi-assistant"]["artifactPlan"] = unsafe_artifacts
        path.write_text(json.dumps(template))
        with pytest.raises(DomainError) as unsafe:
            native._template()
        assert unsafe.value.code == "native_template_mismatch"
