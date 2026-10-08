"""Owner HTTP call preparation and durable one-call binding without provider usage."""

from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from voicebridge.contracts import CallIntentBinding, DomainError
from voicebridge.db import Call, Record, now
from voicebridge.protocol import CALL_INTENT_KIND

from .test_http_providers_knowledge import headers
from .test_provider_transcripts import envelope, send


def configure(app: FastAPI, provider: str) -> None:
    service = app.state.service
    profile = getattr(service.profiles, provider).model_copy(update={"agent_id": "test-agent"})
    service.profiles = service.profiles.model_copy(update={provider: profile})
    service.settings.provider_metadata_capability = True


@pytest.mark.parametrize("provider", ["retell", "vapi"])
def test_http_prepare_bind_retry_and_authenticated_events(app: FastAPI, provider: str):
    configure(app, provider)
    with TestClient(app) as client:
        assert client.post("/api/calls/prepare", json={"provider": provider}).status_code == 401
        assert (
            client.post(
                "/api/calls/prepare",
                json={"provider": provider, "agent_id": "caller-selected"},
                headers=headers(app),
            ).status_code
            == 422
        )
        prepared = client.post(
            "/api/calls/prepare", json={"provider": provider}, headers=headers(app)
        )
        assert prepared.status_code == 200
        data = prepared.json()
        assert data["agent_id"] == "test-agent" and data["provider"] == provider
        assert len(data["capability"]) >= 40
        assert client.get("/api/state", headers=headers(app)).json()["calls"] == []
        bind = {"intent_id": data["intent_id"], "external_id": "test-transcript"}
        first = client.post("/api/calls/bind", json=bind, headers=headers(app))
        assert first.status_code == 200
        assert (
            client.post("/api/calls/bind", json=bind, headers=headers(app)).json() == first.json()
        )
        assert (
            client.post(
                "/api/calls/bind",
                json={**bind, "external_id": "test-other-call"},
                headers=headers(app),
            ).status_code
            == 409
        )
        body = envelope(
            provider,
            "call_started" if provider == "retell" else "status-update",
            data["capability"],
        )
        assert send(client, app, provider, body).status_code == 200
        state = client.get("/api/state", headers=headers(app)).json()
        assert len(state["calls"]) == 1 and state["calls"][0]["id"] == first.json()["call_id"]
        assert state["appointments"] == [] and state["jobs"] == []
        with app.state.service.sessions() as session:
            assert session.scalar(select(Record).where(Record.kind == CALL_INTENT_KIND)) is None


def test_unconfigured_profile_cannot_prepare_native_call(app: FastAPI):
    with TestClient(app) as client:
        assert (
            client.post(
                "/api/calls/prepare", json={"provider": "vapi"}, headers=headers(app)
            ).status_code
            == 403
        )


def test_intent_expiry_capacity_cleanup_and_unknown_binding(app: FastAPI):
    configure(app, "vapi")
    service = app.state.service
    service.settings.max_pending_call_intents = 1
    with TestClient(app) as client:
        data = client.post(
            "/api/calls/prepare", json={"provider": "vapi"}, headers=headers(app)
        ).json()
        assert (
            client.post(
                "/api/calls/prepare", json={"provider": "vapi"}, headers=headers(app)
            ).status_code
            == 429
        )
        with service.sessions.begin() as session:
            row = session.scalar(select(Record).where(Record.key == data["intent_id"]))
            row.value = {**row.value, "expires_at": now().timestamp() - 1}
        binding = {"intent_id": data["intent_id"], "external_id": "test-native-call"}
        assert client.post("/api/calls/bind", json=binding, headers=headers(app)).status_code == 403
        assert (
            client.post(
                "/api/calls/prepare", json={"provider": "vapi"}, headers=headers(app)
            ).status_code
            == 200
        )
        assert client.post("/api/calls/bind", json=binding, headers=headers(app)).status_code == 404
        assert (
            client.post(
                "/api/calls/bind",
                json={"intent_id": "intent-test-unknown", "external_id": "test-native-call"},
                headers=headers(app),
            ).status_code
            == 404
        )


def test_intent_cross_tenant_and_concurrent_retry(app: FastAPI):
    configure(app, "retell")
    service, runner = app.state.service, app.state.providers
    service.seed("other")
    prepared = runner.prepare_intent("northline", "retell")
    binding = CallIntentBinding(intent_id=prepared["intent_id"], external_id="test-native-call")
    with pytest.raises(DomainError, match="call_intent_not_found"):
        runner.bind_intent("other", binding)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: runner.bind_intent("northline", binding), range(2)))
    assert results[0] == results[1]
    with pytest.raises(DomainError, match="call_intent_not_found"):
        runner.bind_intent("other", binding)
    with service.sessions() as session:
        assert len(list(session.scalars(select(Call)))) == 1


def test_native_id_already_registered_cannot_consume_an_intent(app: FastAPI):
    configure(app, "retell")
    runner = app.state.providers
    runner.register("northline", "retell", "test-existing-native-call", "test-agent")
    prepared = runner.prepare_intent("northline", "retell")
    with pytest.raises(DomainError, match="call_already_registered"):
        runner.bind_intent(
            "northline",
            CallIntentBinding(
                intent_id=prepared["intent_id"], external_id="test-existing-native-call"
            ),
        )
    with app.state.service.sessions() as session:
        assert session.scalar(select(Record).where(Record.key == prepared["intent_id"])) is not None


def test_bound_retry_after_preparation_deadline_does_not_issue_capability(
    app: FastAPI, monkeypatch
):
    configure(app, "retell")
    runner = app.state.providers
    prepared = runner.prepare_intent("northline", "retell")
    binding = CallIntentBinding(intent_id=prepared["intent_id"], external_id="test-native-call")
    first = runner.bind_intent("northline", binding)
    from datetime import timedelta

    future = now() + timedelta(seconds=app.state.service.settings.call_intent_seconds + 1)
    monkeypatch.setattr("voicebridge.providers.now", lambda: future)
    assert runner.bind_intent("northline", binding) == first
    assert set(first) == {"call_id"}
