"""Real HTTP provider authentication, terminal lifecycle and durable transcript proof."""

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from voicebridge.protocol import CALL_CAPABILITY_METADATA_KEY

from .test_booking_engine import request
from .test_http_providers_knowledge import headers, signing


def envelope(provider: str, event: str, capability: str) -> dict:
    metadata = {CALL_CAPABILITY_METADATA_KEY: capability}
    if provider == "retell":
        return {
            "event": event,
            "call": {"call_id": "test-transcript", "agent_id": "test-agent", "metadata": metadata},
        }
    return {
        "message": {
            "type": event,
            "call": {"id": "test-transcript", "assistantId": "test-agent", "metadata": metadata},
        }
    }


def send(client: TestClient, app: FastAPI, provider: str, body: dict, extra=None, surface="events"):
    raw = json.dumps(body).encode()
    credential = (
        {"X-Retell-Signature": signing(app, raw)}
        if provider == "retell"
        else {
            "Authorization": "Bearer "
            + app.state.service.settings.vapi_webhook_key.get_secret_value()
        }
    )
    return client.post(
        "/providers/" + provider + "/" + surface,
        content=raw,
        headers={**credential, **(extra or {})},
    )


def snapshot(client: TestClient, app: FastAPI) -> dict:
    return client.get("/api/state", headers=headers(app)).json()["calls"][0]


@pytest.mark.parametrize("provider", ["retell", "vapi"])
def test_metadata_never_replaces_authentication_or_registered_binding(app: FastAPI, provider: str):
    cap = app.state.providers.register("northline", provider, "test-transcript", "test-agent")[
        "capability"
    ]
    body = envelope(provider, "call_started" if provider == "retell" else "status-update", cap)
    with TestClient(app) as client:
        assert send(client, app, provider, body).status_code == 403  # Off by default.
        app.state.service.settings.provider_metadata_capability = True
        assert client.post("/providers/" + provider + "/events", json=body).status_code == 401
        assert (
            send(
                client, app, provider, body, {"X-Call-Capability": "test-wrong-capability"}
            ).status_code
            == 403
        )
        assert send(client, app, provider, body).status_code == 200
        assert send(client, app, provider, body, {"X-Call-Capability": ""}).status_code == 403
        call = body["call"] if provider == "retell" else body["message"]["call"]
        call["metadata"] = {
            CALL_CAPABILITY_METADATA_KEY: "test-wrong-capability",
            "tenant": "other",
        }
        assert send(client, app, provider, body).status_code == 403
        call["metadata"] = {CALL_CAPABILITY_METADATA_KEY: cap}
        call["agent_id" if provider == "retell" else "assistantId"] = "test-other-agent"
        assert send(client, app, provider, body).status_code == 403
        call["agent_id" if provider == "retell" else "assistantId"] = "test-agent"
        call["call_id" if provider == "retell" else "id"] = "test-unregistered-call"
        assert send(client, app, provider, body).status_code == 403


@pytest.mark.parametrize("provider", ["retell", "vapi"])
def test_final_transcript_persists_once_and_late_events_cannot_reopen(app: FastAPI, provider: str):
    app.state.service.settings.provider_metadata_capability = True
    cap = app.state.providers.register("northline", provider, "test-transcript", "test-agent")[
        "capability"
    ]
    body = envelope(provider, "call_ended" if provider == "retell" else "end-of-call-report", cap)
    if provider == "retell":
        body["call"]["transcript_object"] = [
            {"role": "agent", "content": "Confirmed by the business tool."},
            {"role": "user", "content": "Thank you."},
            {"role": "tool_call", "content": {"private": "must not persist"}},
        ]
    else:
        body["message"]["artifact"] = {
            "messages": [
                {"role": "assistant", "message": "Confirmed by the business tool."},
                {"role": "user", "message": "Thank you."},
                {"role": "system", "message": "must not persist"},
            ]
        }
    with TestClient(app) as client:
        assert send(client, app, provider, body).status_code == 200
        assert send(client, app, provider, body).json()["duplicate"] is True
        expected = [
            {"speaker": "assistant", "text": "Confirmed by the business tool."},
            {"speaker": "user", "text": "Thank you."},
        ]
        assert snapshot(client, app)["transcript"] == expected
        assert (
            send(
                client,
                app,
                provider,
                envelope(
                    provider, "call_started" if provider == "retell" else "status-update", cap
                ),
            ).status_code
            == 200
        )
        assert (
            send(
                client,
                app,
                provider,
                envelope(
                    provider, "call_analyzed" if provider == "retell" else "end-of-call-report", cap
                ),
            ).status_code
            == 200
        )
        state = snapshot(client, app)
        assert state["state"] == "ended" and state["transcript"] == expected


def test_vapi_ended_status_retires_tools_before_final_report(app: FastAPI):
    app.state.service.settings.provider_metadata_capability = True
    cap = app.state.providers.register("northline", "vapi", "test-transcript", "test-agent")[
        "capability"
    ]
    body = envelope("vapi", "status-update", cap)
    body["message"]["status"] = "ended"
    with TestClient(app) as client:
        assert send(client, app, "vapi", body).status_code == 200
        assert snapshot(client, app)["state"] == "ended"
        tools = envelope("vapi", "tool-calls", cap)
        tools["message"]["toolCallList"] = [
            {
                "id": "test-tool",
                "function": {"name": "answer_question", "arguments": {"query": "hours"}},
            }
        ]
        assert send(client, app, "vapi", tools, surface="tools").status_code == 403
        ended = envelope("vapi", "end-of-call-report", cap)
        ended["message"]["artifact"] = {"messages": [{"role": "assistant", "message": "Goodbye."}]}
        assert send(client, app, "vapi", ended).status_code == 200
        assert snapshot(client, app)["transcript"] == [{"speaker": "assistant", "text": "Goodbye."}]


@pytest.mark.parametrize("provider", ["retell", "vapi"])
def test_malformed_final_transcript_does_not_retire_or_mutate_call(app: FastAPI, provider: str):
    app.state.service.settings.provider_metadata_capability = True
    cap = app.state.providers.register("northline", provider, "test-transcript", "test-agent")[
        "capability"
    ]
    body = envelope(provider, "call_ended" if provider == "retell" else "end-of-call-report", cap)
    if provider == "retell":
        body["call"]["transcript_object"] = [{"role": "agent", "content": 7}]
    else:
        body["message"]["artifact"] = {"messages": [{"role": "assistant", "message": 7}]}
    with TestClient(app) as client:
        before = snapshot(client, app)
        assert send(client, app, provider, body).status_code == 422
        assert snapshot(client, app) == before


@pytest.mark.parametrize("provider", ["retell", "vapi"])
def test_null_call_metadata_is_a_bounded_client_error(app: FastAPI, provider: str):
    app.state.service.settings.provider_metadata_capability = True
    body = (
        {"call": None, "event": "call_started"}
        if provider == "retell"
        else {"message": {"call": None, "type": "status-update"}}
    )
    with TestClient(app) as client:
        assert send(client, app, provider, body).status_code == 422


@pytest.mark.parametrize("provider", ["retell", "vapi"])
def test_retirement_after_binding_blocks_reservation_under_mutation_lock(
    app: FastAPI, provider: str, monkeypatch
):
    app.state.service.settings.provider_metadata_capability = True
    runner = app.state.providers
    cap = runner.register("northline", provider, "test-transcript", "test-agent")["capability"]
    invoke = runner.invoke

    def retire_before_reservation(tenant, name, args, call_id=None, management=False):
        # Reproduce a second replica retiring the already-authorized call before book().
        runner.event(
            provider,
            envelope(provider, "call_ended" if provider == "retell" else "end-of-call-report", cap),
            cap,
        )
        return invoke(tenant, name, args, call_id, management)

    monkeypatch.setattr(runner, "invoke", retire_before_reservation)
    body = envelope(provider, "tool-calls", cap)
    args = request(app).model_dump(mode="json", exclude={"call_id"})
    if provider == "retell":
        body.update(name="create_booking", args=args)
    else:
        body["message"]["toolCallList"] = [
            {"id": "test-tool", "function": {"name": "create_booking", "arguments": args}}
        ]
    with TestClient(app) as client:
        response = send(client, app, provider, body, surface="tools")
        if provider == "retell":
            assert response.status_code == 403
        else:
            assert response.json()["results"][0]["error"] == "call_not_active"
        state = client.get("/api/state", headers=headers(app)).json()
        assert state["appointments"] == [] and state["jobs"] == []


@pytest.mark.parametrize("provider", ["retell", "vapi"])
@pytest.mark.parametrize("name", ["answer_question", "check_availability"])
def test_retirement_after_binding_blocks_read_tools(
    app: FastAPI, provider: str, name: str, monkeypatch
):
    app.state.service.settings.provider_metadata_capability = True
    runner = app.state.providers
    cap = runner.register("northline", provider, "test-transcript", "test-agent")["capability"]
    invoke = runner.invoke

    def retire_then_read(tenant, tool_name, args, call_id=None, management=False):
        runner.event(
            provider,
            envelope(provider, "call_ended" if provider == "retell" else "end-of-call-report", cap),
            cap,
        )
        return invoke(tenant, tool_name, args, call_id, management)

    monkeypatch.setattr(runner, "invoke", retire_then_read)
    args = (
        {"query": "warranty"}
        if name == "answer_question"
        else {"start": request(app).start.isoformat(), "service": request(app).service}
    )
    body = envelope(provider, "tool-calls", cap)
    if provider == "retell":
        body.update(name=name, args=args)
    else:
        body["message"]["toolCallList"] = [
            {"id": "test-read", "function": {"name": name, "arguments": args}}
        ]
    with TestClient(app) as client:
        response = send(client, app, provider, body, surface="tools")
        if provider == "retell":
            assert response.status_code == 403
        else:
            assert response.json()["results"][0]["error"] == "call_not_active"


def test_vapi_rechecks_each_batch_entry_after_retirement(app: FastAPI, monkeypatch):
    runner = app.state.providers
    app.state.service.settings.provider_metadata_capability = True
    cap = runner.register("northline", "vapi", "test-transcript", "test-agent")["capability"]
    invoke = runner.invoke
    count = 0

    def retire_after_first(tenant, name, args, call_id=None, management=False):
        nonlocal count
        result = invoke(tenant, name, args, call_id, management)
        count += 1
        if count == 1:
            runner.event("vapi", envelope("vapi", "end-of-call-report", cap), cap)
        return result

    monkeypatch.setattr(runner, "invoke", retire_after_first)
    body = envelope("vapi", "tool-calls", cap)
    body["message"]["toolCallList"] = [
        {
            "id": "test-read-" + str(i),
            "function": {"name": "answer_question", "arguments": {"query": "warranty"}},
        }
        for i in range(2)
    ]
    with TestClient(app) as client:
        results = send(client, app, "vapi", body, surface="tools").json()["results"]
        assert "result" in results[0]
        assert results[1]["error"] == "call_not_active"
