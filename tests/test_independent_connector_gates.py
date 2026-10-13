"""A free business connector cannot authorize another service or a voice charge."""

import httpx
import pytest
from fastapi import FastAPI
from pydantic import ValidationError
from voicebridge.connectors import Delivery, GoogleCalendar, RemoteTransport
from voicebridge.contracts import DomainError
from voicebridge.settings import ProviderSettings


def test_connectors_are_independently_disabled_by_default(app: FastAPI) -> None:
    settings = app.state.service.settings.provider
    assert not settings.calendar_enabled
    assert not settings.crm_enabled
    assert not settings.voice_enabled


def test_legacy_global_switch_cannot_enable_all_services(app: FastAPI) -> None:
    value = app.state.service.settings.provider.model_dump()
    value["enabled"] = True
    with pytest.raises(ValidationError, match="independent"):
        ProviderSettings.model_validate(value)


def test_calendar_permission_cannot_enable_crm_or_voice(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = app.state.service.settings.model_copy(
        update={
            "provider": app.state.service.settings.provider.model_copy(
                update={"calendar_enabled": True}
            )
        }
    )
    calls = []

    def respond(self, method, url, **kwargs):
        calls.append(url)
        return httpx.Response(200, json={"items": []})

    monkeypatch.setattr(httpx.Client, "request", respond)
    calendar_url = GoogleCalendar(settings).url()
    RemoteTransport(settings, "calendar").request("GET", calendar_url, {})
    with pytest.raises(DomainError, match="external_execution_disabled"):
        RemoteTransport(settings, "crm").request("GET", settings.provider.contacts_path, {})
    with pytest.raises(DomainError, match="external_execution_disabled"):
        RemoteTransport(settings, "voice").request("GET", settings.provider.retell_base_url, {})
    assert calls == [calendar_url]


def test_connector_scope_rejects_another_service_destination(app: FastAPI) -> None:
    settings = app.state.service.settings.model_copy(
        update={
            "provider": app.state.service.settings.provider.model_copy(
                update={"calendar_enabled": True}
            )
        }
    )
    with pytest.raises(DomainError, match="connector_destination_denied"):
        RemoteTransport(settings, "calendar").request("GET", settings.provider.contacts_path, {})


def test_crm_stays_local_when_only_calendar_enabled(app: FastAPI) -> None:
    settings = app.state.service.settings.model_copy(
        update={
            "provider": app.state.service.settings.provider.model_copy(
                update={"calendar_enabled": True}
            )
        }
    )
    delivery = Delivery(settings, app.state.service.sessions)
    assert delivery.crm("test-local-crm", {"email": "owner@test.invalid"}) == "test-local-crm"


def test_capture_mode_cannot_deliver_to_real_mailbox(app: FastAPI) -> None:
    with pytest.raises(DomainError, match="synthetic_recipient_required"):
        app.state.worker.delivery.followup("test-denied", {"email": "owner@example.com"})


@pytest.mark.parametrize(
    "escape", ["../deals", "%2e%2e/deals", "%252e%252e/deals", "%2f..%2fdeals"]
)
def test_destination_rejects_normalized_and_encoded_path_escape(app: FastAPI, escape: str) -> None:
    settings = app.state.service.settings.model_copy(
        update={
            "provider": app.state.service.settings.provider.model_copy(update={"crm_enabled": True})
        }
    )
    with pytest.raises(DomainError, match="connector_destination_denied"):
        RemoteTransport(settings, "crm").request(
            "GET", settings.provider.contacts_path + "/" + escape, {}
        )


def test_synthetic_evaluation_refuses_live_calendar(app: FastAPI) -> None:
    app.state.service.settings.provider = app.state.service.settings.provider.model_copy(
        update={"calendar_enabled": True}
    )
    with pytest.raises(DomainError, match="synthetic_evaluation_required"):
        app.state.providers.evaluate(app.state.service.settings.tenant_id)


def test_destination_rejects_final_segment_parameters(app: FastAPI) -> None:
    settings = app.state.service.settings.model_copy(
        update={
            "provider": app.state.service.settings.provider.model_copy(update={"crm_enabled": True})
        }
    )
    with pytest.raises(DomainError, match="connector_destination_denied"):
        RemoteTransport(settings, "crm").request(
            "GET", settings.provider.contacts_path + ";outside", {}
        )
