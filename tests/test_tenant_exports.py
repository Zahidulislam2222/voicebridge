"""Real OIDC/HTTP/PostgreSQL isolation for bounded owner downloads."""

import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from voicebridge.db import (
    Appointment,
    Audit,
    AuthSession,
    Call,
    Contact,
    Document,
    Job,
    Record,
    now,
    tenant_lock,
)

from .test_oidc_sessions import configured, login
from .test_oidc_sessions import issuer as issuer


def fixture_records(app: FastAPI) -> None:
    with app.state.service.sessions.begin() as session:
        for tenant, label in [("northline", "own"), ("test-other-tenant", "foreign")]:
            session.add(
                Contact(
                    id=label + "-contact",
                    tenant_id=tenant,
                    name=label + "-visible-contact",
                    email=label + "@example.invalid",
                    phone="+15555550123",
                    notes="",
                )
            )
            session.add(
                Call(
                    id=label + "-call",
                    tenant_id=tenant,
                    provider="retell",
                    external_id="test-" + label,
                    agent_id="test-agent",
                    capability_digest="test-private-capability-digest",
                    state="ended",
                    transcript=[{"speaker": "user", "text": label + "-private-transcript"}],
                )
            )
            session.add(
                Document(
                    id=label + "-document",
                    tenant_id=tenant,
                    name=label + "-visible-document",
                    text=label + "-visible-knowledge",
                    checksum="test-checksum",
                )
            )
            session.add(
                Record(
                    id=label + "-private-record",
                    tenant_id=tenant,
                    kind="private_fixture",
                    key="test-private-key",
                    value={"grant": "test-private-grant"},
                )
            )
            session.add(
                Job(
                    id=label + "-job",
                    tenant_id=tenant,
                    kind="crm",
                    operation_key="test-" + label,
                    payload={"test-private-payload": "test-private-provider-url"},
                    status="dead",
                    detail="known_pre_send_failure",
                )
            )
        session.flush()
        for tenant, label in [("northline", "own"), ("test-other-tenant", "foreign")]:
            session.add(
                Appointment(
                    id=label + "-booking",
                    tenant_id=tenant,
                    contact_id=label + "-contact",
                    call_id=label + "-call",
                    service="Appliance repair",
                    start=now() + timedelta(days=2),
                    end=now() + timedelta(days=2, hours=1),
                    status="confirmed",
                )
            )


def authorized(
    client: TestClient, issuer: dict[str, Any], subject: str = "test-owner"
) -> dict[str, str]:
    issuer["subject"] = subject
    issuer["email"] = (
        "owner@example.invalid" if subject == "test-owner" else subject + "@example.invalid"
    )
    assert login(client, issuer).status_code == 303
    return {
        "Origin": "http://localhost:18080",
        "X-CSRF-Token": client.get("/auth/session").json()["csrf"],
    }


def test_two_real_oidc_tenants_export_only_allowlisted_own_records(
    app: FastAPI, issuer: dict[str, Any], tmp_path: Path
) -> None:
    instance = configured(app, issuer, tmp_path)
    fixture_records(instance)
    with TestClient(instance) as owner, TestClient(instance) as other:
        own_headers = authorized(owner, issuer)
        other_headers = authorized(other, issuer, "test-other")
        for client, headers, label, forbidden in [
            (owner, own_headers, "own", "foreign"),
            (other, other_headers, "foreign", "own"),
        ]:
            visible = client.get("/api/state")
            assert label + "-visible-contact" in visible.text
            assert forbidden + "-visible" not in visible.text
            denied_job = client.post("/api/jobs/" + forbidden + "-job/replay", headers=headers)
            missing_job = client.post("/api/jobs/test-missing/replay", headers=headers)
            assert denied_job.status_code == missing_job.status_code == 404
            response = client.post("/api/exports/snapshot", json={}, headers=headers)
            assert response.status_code == 200
            result = response.json()
            assert label + "-visible-contact" in response.text
            assert forbidden + "-visible" not in response.text
            assert label + "-job" in response.text and forbidden + "-job" not in response.text
            assert "private-transcript" not in response.text
            for forbidden_field in (
                "test-private",
                '"payload"',
                '"capability_digest"',
                '"tenant_id"',
                '"transcript"',
                '"auth_sessions"',
                '"provider_url"',
            ):
                assert forbidden_field not in response.text
            assert result["counts"]["contacts"] == 1
            assert result["truncated"]["contacts"] is False
            assert response.headers["content-disposition"].startswith('attachment; filename="')
            assert response.headers["content-type"] == "application/json"
            assert response.headers["cache-control"] == "no-store"
            assert response.headers["x-content-type-options"] == "nosniff"
            transcript = client.post(
                "/api/calls/" + label + "-call/transcript-export", json={}, headers=headers
            )
            assert transcript.status_code == 200
            assert label + "-private-transcript" in transcript.text
            missing = client.post(
                "/api/calls/test-missing/transcript-export", json={}, headers=headers
            )
            foreign = client.post(
                "/api/calls/" + forbidden + "-call/transcript-export", json={}, headers=headers
            )
            assert (
                foreign.status_code == missing.status_code == 404
                and foreign.json() == missing.json()
            )


@pytest.mark.parametrize("subject", ["test-viewer", "test-operator"])
def test_nonowners_cannot_download(
    app: FastAPI, issuer: dict[str, Any], tmp_path: Path, subject: str
) -> None:
    instance = configured(app, issuer, tmp_path)
    with TestClient(instance) as client:
        headers = authorized(client, issuer, subject)
        for path in ["/api/exports/snapshot", "/api/calls/test-call/transcript-export"]:
            assert client.post(path, json={}, headers=headers).status_code == 403


def test_export_rejects_anonymous_csrf_origin_tenant_selectors_and_logout(
    app: FastAPI, issuer: dict[str, Any], tmp_path: Path
) -> None:
    instance = configured(app, issuer, tmp_path)
    with TestClient(instance) as client:
        assert client.post("/api/exports/snapshot", json={}).status_code == 401
        assert (
            client.post(
                "/api/exports/snapshot",
                json={},
                headers={
                    "Authorization": "Bearer "
                    + instance.state.service.settings.operator_key.get_secret_value()
                },
            ).status_code
            == 401
        )
        headers = authorized(client, issuer)
        assert (
            client.post(
                "/api/exports/snapshot", json={}, headers={"Origin": headers["Origin"]}
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/api/exports/snapshot",
                json={},
                headers={**headers, "Origin": "https://untrusted.example.invalid"},
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/api/exports/snapshot", json={"tenant_id": "test-other-tenant"}, headers=headers
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/exports/snapshot?tenant_id=test-other-tenant", json={}, headers=headers
            ).status_code
            == 422
        )
        assert client.post("/auth/logout", headers=headers).status_code == 204
        assert client.post("/api/exports/snapshot", json={}, headers=headers).status_code == 401
    with instance.state.service.sessions() as session:
        assert not list(session.scalars(select(Audit).where(Audit.action.like("export.%"))))


def test_expired_session_cannot_generate_export(
    app: FastAPI, issuer: dict[str, Any], tmp_path: Path
) -> None:
    instance = configured(app, issuer, tmp_path)
    with TestClient(instance) as client:
        headers = authorized(client, issuer)
        with instance.state.service.sessions.begin() as session:
            for row in session.scalars(select(AuthSession).where(AuthSession.kind == "session")):
                row.expires = now() - timedelta(seconds=1)
        assert client.post("/api/exports/snapshot", json={}, headers=headers).status_code == 401


def test_snapshot_truncation_order_byte_cap_and_success_audit(app: FastAPI) -> None:
    service = app.state.service
    with service.sessions.begin() as session:
        for index in range(3):
            session.add(
                Contact(
                    id=str(3 - index),
                    tenant_id="northline",
                    name="test-contact",
                    email=f"test{index}@example.invalid",
                    phone="+15555550123",
                    notes="",
                )
            )
    service.settings = service.settings.model_copy(update={"max_records_per_page": 2})
    result = service.export_snapshot("northline")
    assert [row.id for row in result.contacts] == ["1", "2"]
    assert result.counts["contacts"] == 3 and result.truncated["contacts"] is True
    with service.sessions() as session:
        assert (
            len(
                list(
                    session.scalars(
                        select(Audit).where(Audit.action == "export.snapshot.generated")
                    )
                )
            )
            == 1
        )
    service.settings = service.settings.model_copy(update={"export_max_bytes": 10})
    from voicebridge.contracts import DomainError

    with pytest.raises(DomainError, match="export_too_large"):
        service.export_snapshot("northline")
    with service.sessions() as session:
        assert (
            len(
                list(
                    session.scalars(
                        select(Audit).where(Audit.action == "export.snapshot.generated")
                    )
                )
            )
            == 1
        )


def test_redacted_stale_text_cannot_escape_either_export_or_state(app: FastAPI) -> None:
    service = app.state.service
    with service.sessions.begin() as session:
        session.add(
            Call(
                id="test-redacted",
                tenant_id="northline",
                provider="retell",
                external_id="test-redacted",
                agent_id="test-agent",
                capability_digest="test-fake-digest",
                state="ended",
                transcript=[{"speaker": "user", "text": "test-private-stale-text"}],
            )
        )
        session.add(
            Record(
                id="test-tombstone",
                tenant_id="northline",
                kind="call_redaction",
                key="test-redacted",
                value={"redacted_at": now().isoformat()},
            )
        )
    transcript = service.export_transcript("northline", "test-redacted")
    assert transcript.redacted is True and transcript.transcript == []
    assert "test-private-stale-text" not in service.export_snapshot("northline").model_dump_json()
    assert "test-private-stale-text" not in json.dumps(service.snapshot("northline"))


def test_active_and_empty_transcript_are_explicit(app: FastAPI) -> None:
    from voicebridge.contracts import DomainError

    service = app.state.service
    with service.sessions.begin() as session:
        session.add(
            Call(
                id="test-empty",
                tenant_id="northline",
                provider="retell",
                external_id="test-empty",
                agent_id="test-agent",
                capability_digest="test-fake-digest",
                state="registered",
                transcript=[],
            )
        )
    with pytest.raises(DomainError, match="call_not_ended"):
        service.export_transcript("northline", "test-empty")
    with service.sessions.begin() as session:
        session.get(Call, "test-empty").state = "ended"
    result = service.export_transcript("northline", "test-empty")
    assert result.redacted is False and result.transcript == []


def test_export_waits_for_redaction_commit_and_reads_the_tombstone(app: FastAPI) -> None:
    service = app.state.service
    with service.sessions.begin() as session:
        session.add(
            Call(
                id="test-race",
                tenant_id="northline",
                provider="retell",
                external_id="test-race",
                agent_id="test-agent",
                capability_digest="test-fake-digest",
                state="ended",
                transcript=[{"speaker": "user", "text": "test-private-before-redaction"}],
            )
        )
    with ThreadPoolExecutor(max_workers=1) as pool:
        with service.sessions.begin() as session:
            tenant_lock(session, "northline")
            session.get(Call, "test-race").transcript = []
            session.add(
                Record(
                    id="test-race-marker",
                    tenant_id="northline",
                    kind="call_redaction",
                    key="test-race",
                    value={"redacted_at": now().isoformat()},
                )
            )
            session.flush()
            future = pool.submit(service.export_transcript, "northline", "test-race")
            waiting = False
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline and not future.done():
                session.execute(text("SELECT pg_stat_clear_snapshot()"))
                waiting = bool(
                    session.scalar(
                        text(
                            "SELECT count(*) FROM pg_stat_activity "
                            "WHERE datname=current_database() AND wait_event_type='Lock'"
                        )
                    )
                )
                if waiting:
                    break
                time.sleep(0.02)
            assert waiting, "The artifact reader must wait for concurrent redaction"
        result = future.result(timeout=5)
    assert result.redacted is True and result.transcript == []


@pytest.mark.parametrize("provider", ["retell", "vapi"])
def test_late_terminal_event_never_repopulates_export(app: FastAPI, provider: str) -> None:
    from .test_provider_transcripts import envelope

    providers, service = app.state.providers, app.state.service
    registered = providers.register("northline", provider, "test-transcript", "test-agent")
    terminal = "call_ended" if provider == "retell" else "end-of-call-report"
    value = envelope(provider, terminal, registered["capability"])
    if provider == "retell":
        value["call"]["transcript"] = "test-private-original"
    else:
        value["message"]["artifact"] = {"transcript": "test-private-original"}
    providers.event(provider, value, registered["capability"])
    service.redact_call_transcript("northline", registered["call_id"])
    if provider == "retell":
        value["call"]["transcript"] = "test-private-late"
    else:
        value["message"]["artifact"] = {"transcript": "test-private-late"}
    providers.event(provider, value, registered["capability"])
    exported = service.export_transcript("northline", registered["call_id"])
    assert exported.redacted is True and exported.transcript == []
    assert "test-private" not in service.export_snapshot("northline").model_dump_json()


@pytest.mark.parametrize(
    "filename", ["../private.json", "file.json\r\nX-Test: injected", "file.json\n", "file.txt"]
)
def test_attachment_filenames_are_strict_configuration(app: FastAPI, filename: str) -> None:
    from pydantic import ValidationError
    from voicebridge.settings import Settings

    values = app.state.service.settings.model_dump()
    for field in ["export_snapshot_filename", "export_transcript_filename"]:
        with pytest.raises(ValidationError):
            Settings.model_validate({**values, field: filename})


def test_transcript_byte_cap_and_revoked_policy(
    app: FastAPI, issuer: dict[str, Any], tmp_path: Path
) -> None:
    instance = configured(app, issuer, tmp_path)
    fixture_records(instance)
    with TestClient(instance) as client:
        headers = authorized(client, issuer)
        instance.state.service.settings = instance.state.service.settings.model_copy(
            update={"export_max_bytes": 10}
        )
        result = client.post("/api/calls/own-call/transcript-export", json={}, headers=headers)
        assert result.status_code == 413 and result.json() == {"error": "export_too_large"}
        policy = json.loads(instance.state.service.settings.auth.access_file.read_text())
        policy["bindings"][0]["role"] = "viewer"
        instance.state.service.settings.auth.access_file.write_text(json.dumps(policy))
        assert client.post("/api/exports/snapshot", json={}, headers=headers).status_code == 403
    with instance.state.service.sessions() as session:
        assert not list(session.scalars(select(Audit).where(Audit.action.like("export.%"))))


@pytest.mark.parametrize("page_limit", [1, 20])
def test_collection_count_and_rows_share_one_observation_under_insert(
    app: FastAPI, page_limit: int
) -> None:
    from sqlalchemy import event

    service = app.state.service
    service.settings = service.settings.model_copy(update={"max_records_per_page": page_limit})
    with service.sessions.begin() as session:
        session.add(
            Contact(
                id="z",
                tenant_id="northline",
                name="test-original",
                email="test-original@example.invalid",
                phone="+15555550123",
            )
        )
    engine = service.sessions.kw["bind"]
    injected = False

    def insert_after_contact_query(
        _connection: Any, _cursor: Any, statement: str, _parameters: Any, _context: Any, _many: bool
    ) -> None:
        nonlocal injected
        if not injected and "from contacts" in statement.lower():
            injected = True
            with service.sessions.begin() as session:
                session.add(
                    Contact(
                        id="a",
                        tenant_id="northline",
                        name="test-concurrent",
                        email="test-concurrent@example.invalid",
                        phone="+15555550123",
                    )
                )

    event.listen(engine, "after_cursor_execute", insert_after_contact_query)
    try:
        result = service.export_snapshot("northline")
    finally:
        event.remove(engine, "after_cursor_execute", insert_after_contact_query)
    assert injected
    ids = [row.id for row in result.contacts]
    if result.counts["contacts"] == 1:
        assert ids == ["z"] and result.truncated["contacts"] is False
    else:
        assert result.counts["contacts"] == 2
        assert ids == ["a", "z"][:page_limit]
        assert result.truncated["contacts"] is (page_limit == 1)
    with service.sessions() as session:
        assert len(list(session.scalars(select(Contact)))) == 2
