import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from voicebridge.api import create_app
from voicebridge.connectors import Delivery


def test_api_identity_uses_maintained_product_data(app: FastAPI, tmp_path: Path) -> None:
    settings = app.state.service.settings
    profile = json.loads(settings.profile_file.read_text())
    profile["application_name"] = "Configured test application"
    path = tmp_path / "test-profile.json"
    path.write_text(json.dumps(profile))
    instance = create_app(settings.model_copy(update={"profile_file": path}))
    try:
        assert instance.title == "Configured test application"
        assert instance.version == app.version
    finally:
        instance.state.service.sessions.kw["bind"].dispose()


def test_captured_message_identity_uses_configured_sender_domain(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    import smtplib

    settings = app.state.service.settings.model_copy(
        update={"smtp_from": "capture@test-sender.invalid"}
    )
    messages = []

    class Capture:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args: object) -> None:
            pass

        def send_message(self, message):
            messages.append(message)

    monkeypatch.setattr(smtplib, "SMTP", Capture)
    Delivery(settings, app.state.service.sessions).followup(
        "test-message-operation",
        {
            "booking_id": "test-booking",
            "name": "Synthetic customer",
            "service": "Test service",
            "start": "test-start",
            "timezone": "test-timezone",
            "email": "recipient@test.invalid",
        },
    )
    assert messages[0]["Message-ID"].endswith("@test-sender.invalid>")
