"""Owner redaction is tenant scoped and survives late provider events."""

from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from voicebridge.db import Audit, Call, Record

from .test_oidc_sessions import configured, login
from .test_oidc_sessions import issuer as issuer
from .test_provider_transcripts import envelope


@pytest.mark.parametrize("provider", ["retell", "vapi"])
def test_owner_redacts_ended_transcript_once_and_late_event_cannot_restore(
    app: FastAPI, issuer: dict[str, Any], tmp_path: Path, provider: str
) -> None:
    instance = configured(app, issuer, tmp_path)
    tenant = instance.state.service.settings.tenant_id
    registered = instance.state.providers.register(
        tenant, provider, "test-redaction", "test-agent"
    )
    call_id, capability = registered["call_id"], registered["capability"]
    terminal = "call_ended" if provider == "retell" else "end-of-call-report"
    first = envelope(provider, terminal, capability)
    if provider == "retell":
        first["call"]["call_id"] = "test-redaction"
        first["call"]["transcript"] = "Sensitive spoken words"
    else:
        first["message"]["call"]["id"] = "test-redaction"
        first["message"]["artifact"] = {"transcript": "Sensitive spoken words"}
    path = f"/api/calls/{call_id}/transcript"
    with TestClient(instance) as client:
        assert client.delete(path).status_code == 401
        assert login(client, issuer).status_code == 303
        csrf = client.get("/auth/session").json()["csrf"]
        headers = {"Origin": "http://localhost:18080", "X-CSRF-Token": csrf}
        assert client.delete(path).status_code == 403
        assert client.delete(path, headers=headers).status_code == 409
        assert instance.state.providers.event(provider, first, capability)["accepted"]
        assert client.get("/api/state").json()["calls"][0]["transcript"]
        assert client.delete(path, headers=headers).status_code == 204
        assert client.delete(path, headers=headers).status_code == 204
        assert client.get("/api/state").json()["calls"][0]["transcript"] == []

        late = envelope(provider, terminal, capability)
        if provider == "retell":
            late["call"]["call_id"] = "test-redaction"
            late["call"]["transcript"] = "Later spoken words"
        else:
            late["message"]["call"]["id"] = "test-redaction"
            late["message"]["artifact"] = {"transcript": "Later spoken words"}
        assert instance.state.providers.event(provider, late, capability)["accepted"]
        assert client.get("/api/state").json()["calls"][0]["transcript"] == []

    with instance.state.service.sessions() as session:
        call = session.get(Call, call_id)
        marker = session.scalar(
            select(Record).where(Record.kind == "call_redaction", Record.key == call_id)
        )
        actions = list(
            session.scalars(
                select(Audit).where(Audit.action == "call.transcript.redacted")
            )
        )
        assert call is not None and call.transcript == []
        assert marker is not None and marker.tenant_id == tenant
        assert len(actions) == 1


def test_redaction_denies_other_tenant_and_non_owner(
    app: FastAPI, issuer: dict[str, Any], tmp_path: Path
) -> None:
    instance = configured(app, issuer, tmp_path)
    other = instance.state.providers.register(
        "test-other-tenant", "retell", "test-other-call", "test-agent"
    )
    call_id, capability = other["call_id"], other["capability"]
    ended = envelope("retell", "call_ended", capability)
    ended["call"]["call_id"] = "test-other-call"
    ended["call"]["transcript"] = "Other tenant words"
    instance.state.providers.event("retell", ended, capability)
    path = f"/api/calls/{call_id}/transcript"
    with TestClient(instance) as client:
        assert login(client, issuer).status_code == 303
        csrf = client.get("/auth/session").json()["csrf"]
        headers = {"Origin": "http://localhost:18080", "X-CSRF-Token": csrf}
        assert client.delete(path, headers=headers).status_code == 404
    issuer.update(subject="test-operator", email="test-operator@example.invalid")
    with TestClient(instance) as client:
        assert login(client, issuer).status_code == 303
        csrf = client.get("/auth/session").json()["csrf"]
        headers = {"Origin": "http://localhost:18080", "X-CSRF-Token": csrf}
        assert client.delete(path, headers=headers).status_code == 403
    with instance.state.service.sessions() as session:
        call = session.get(Call, call_id)
        assert call is not None and call.transcript
