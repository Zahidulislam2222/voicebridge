"""External mail needs its own permission, recipient boundary and verified TLS."""

import smtplib
import ssl

import pytest
from fastapi import FastAPI
from pydantic import SecretStr, ValidationError
from voicebridge.connectors import Delivery, RetryableFailure, UnknownOutcome
from voicebridge.contracts import DomainError
from voicebridge.settings import Settings


def delivery(app, **overrides):
    settings = app.state.service.settings.model_copy(
        update={
            "followup_transport": "smtp",
            "external_delivery_enabled": True,
            "followup_recipients": ["owner@example.com"],
            "smtp_from": "sender@example.com",
            "smtp_username": "sender@example.com",
            "smtp_password": SecretStr("test-key"),
            "smtp_security": "tls",
            **overrides,
        }
    )
    return Delivery(settings, app.state.service.sessions)


def payload():
    return {
        "email": "owner@example.com",
        "name": "Test owner",
        "service": "Test service",
        "start": "test-start",
        "timezone": "test-zone",
        "booking_id": "test-booking",
    }


def fake_smtp(monkeypatch, *, fail=None, refused=None):
    events = []

    class SMTP:
        def __init__(self, *args, **kwargs):
            events.append(("connect", kwargs.get("context")))
            if fail == "connect":
                raise OSError("test connection unavailable")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            if fail == "quit":
                raise OSError("test quit unavailable")

        def ehlo(self):
            events.append(("ehlo", None))

        def starttls(self, *, context):
            events.append(("starttls", context))

        def login(self, username, password):
            events.append(("login", None))
            if fail == "login":
                raise smtplib.SMTPAuthenticationError(535, b"test denied")

        def send_message(self, message):
            events.append(("send", message))
            if fail == "send":
                raise OSError("test ambiguous send")
            if fail == "sender":
                raise smtplib.SMTPSenderRefused(550, b"test rejected", "sender@example.com")
            if fail == "data":
                raise smtplib.SMTPDataError(550, b"test rejected")
            if fail == "temporary":
                raise smtplib.SMTPDataError(451, b"test unavailable")
            return refused or {}

    monkeypatch.setattr(smtplib, "SMTP_SSL", SMTP)
    monkeypatch.setattr(smtplib, "SMTP", SMTP)
    return events


def test_external_smtp_is_disabled_by_default(app: FastAPI) -> None:
    assert not app.state.service.settings.external_delivery_enabled


def test_smtp_selection_without_permission_cannot_send(app: FastAPI) -> None:
    with pytest.raises(DomainError, match="external_delivery_disabled"):
        delivery(app, external_delivery_enabled=False).followup("test-op", payload())


@pytest.mark.parametrize(
    "recipient",
    [
        "other@example.com",
        "owner@example.com,other@example.com",
        "owner@example.com\r\nBcc: other@example.com",
    ],
)
def test_external_recipient_must_be_one_allowlisted_mailbox(app, recipient):
    with pytest.raises(DomainError, match="recipient_not_authorized"):
        delivery(app).followup("test-op", {**payload(), "email": recipient})


@pytest.mark.parametrize("security", ["tls", "starttls"])
def test_tls_and_authentication_precede_send(app, monkeypatch, security):
    events = fake_smtp(monkeypatch)
    assert delivery(app, smtp_security=security).followup("test-op", payload()) == "test-op"
    names = [e[0] for e in events]
    assert names.index("login") < names.index("send")
    contexts = [value for name, value in events if name in {"connect", "starttls"} and value]
    assert contexts and all(
        c.check_hostname and c.verify_mode == ssl.CERT_REQUIRED for c in contexts
    )
    if security == "starttls":
        assert names.index("starttls") < names.index("login")


@pytest.mark.parametrize(
    "failure,error",
    [("connect", RetryableFailure), ("login", DomainError), ("send", UnknownOutcome)],
)
def test_smtp_failure_classification_never_blindly_retries_send(app, monkeypatch, failure, error):
    events = fake_smtp(monkeypatch, fail=failure)
    with pytest.raises(error):
        delivery(app).followup("test-op", payload())
    if failure != "send":
        assert "send" not in [event[0] for event in events]


def test_quit_failure_after_acceptance_preserves_receipt(app, monkeypatch):
    fake_smtp(monkeypatch, fail="quit")
    assert delivery(app).followup("test-op", payload()) == "test-op"


def test_smtp_refusal_is_not_success(app, monkeypatch):
    fake_smtp(monkeypatch, refused={"owner@example.com": (550, b"test denied")})
    with pytest.raises(DomainError, match="followup_recipient_refused"):
        delivery(app).followup("test-op", payload())


@pytest.mark.parametrize("failure", ["sender", "data"])
def test_explicit_smtp_rejection_is_not_an_unknown_send(app, monkeypatch, failure):
    fake_smtp(monkeypatch, fail=failure)
    with pytest.raises(DomainError, match="followup_rejected"):
        delivery(app).followup("test-op", payload())


def test_temporary_data_rejection_is_safe_to_retry(app, monkeypatch):
    fake_smtp(monkeypatch, fail="temporary")
    with pytest.raises(RetryableFailure, match="smtp_temporarily_rejected"):
        delivery(app).followup("test-op", payload())


def test_external_delivery_configuration_requires_credentials_and_recipients(app):
    value = app.state.service.settings.model_dump()
    value.update(followup_transport="smtp", external_delivery_enabled=True)
    with pytest.raises(ValidationError, match="SMTP"):
        Settings.model_validate(value)


def test_disabling_external_delivery_also_requires_capture_transport(app):
    value = app.state.service.settings.model_dump()
    value.update(followup_transport="smtp", external_delivery_enabled=False)
    with pytest.raises(ValidationError, match="SMTP delivery requires permission"):
        Settings.model_validate(value)
    value.update(followup_transport="capture", followup_recipients=[])
    assert Settings.model_validate(value).external_delivery_enabled is False
