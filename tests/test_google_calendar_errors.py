import httpx
import pytest
from fastapi import FastAPI
from voicebridge.connectors import GoogleCalendar, RetryableFailure
from voicebridge.contracts import DomainError


def calendar(app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> GoogleCalendar:
    settings = app.state.service.settings
    instance = GoogleCalendar(
        settings.model_copy(
            update={
                "provider": settings.provider.model_copy(update={"enabled": True}),
            }
        )
    )
    monkeypatch.setattr(instance, "headers", lambda: {"Authorization": "Bearer test-key"})
    return instance


def test_missing_calendar_list_cannot_report_slot_available(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    instance = calendar(app, monkeypatch)
    monkeypatch.setattr(httpx.Client, "request", lambda *args, **kwargs: httpx.Response(404))
    with pytest.raises(DomainError, match="connector"):
        instance.available("test-start", "test-end")


def test_missing_event_requires_accessible_calendar_before_inferring_absence(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    instance = calendar(app, monkeypatch)
    monkeypatch.setattr(httpx.Client, "request", lambda *args, **kwargs: httpx.Response(404))
    with pytest.raises(DomainError, match="connector"):
        instance.get("test-event")


def test_repeat_delete_accepts_documented_deleted_reason(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    instance = calendar(app, monkeypatch)
    monkeypatch.setattr(instance, "get", lambda key: None)
    monkeypatch.setattr(
        httpx.Client,
        "request",
        lambda *args, **kwargs: httpx.Response(
            410,
            json={"error": {"errors": [{"reason": "deleted"}]}},
        ),
    )
    assert instance.put("test-event", {"status": "cancelled", "revision": 2}) == "test-event"


@pytest.mark.parametrize(
    "body",
    [
        {"error": {"errors": [{"reason": "fullSyncRequired"}]}},
        {"error": None},
        {"error": []},
    ],
)
def test_other_gone_errors_cannot_manufacture_delete_success(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch, body: dict
) -> None:
    instance = calendar(app, monkeypatch)
    monkeypatch.setattr(instance, "get", lambda key: None)
    monkeypatch.setattr(
        httpx.Client, "request", lambda *args, **kwargs: httpx.Response(410, json=body)
    )
    with pytest.raises(DomainError, match="connector"):
        instance.put("test-event", {"status": "cancelled", "revision": 2})


@pytest.mark.parametrize("body", [b"invalid-json", b"[]"])
def test_invalid_oauth_response_is_known_presend_failure(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch, body: bytes
) -> None:
    settings = app.state.service.settings
    instance = GoogleCalendar(
        settings.model_copy(
            update={
                "provider": settings.provider.model_copy(update={"enabled": True}),
            }
        )
    )
    monkeypatch.setattr(
        httpx.Client, "post", lambda *args, **kwargs: httpx.Response(200, content=body)
    )
    with pytest.raises(RetryableFailure):
        instance.headers()
