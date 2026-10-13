"""CRM completion requires an unambiguous contact and matching provider readback."""

import httpx
import pytest
from fastapi import FastAPI
from voicebridge.connectors import Delivery, UnknownOutcome
from voicebridge.contracts import DomainError


def configured(app):
    settings = app.state.service.settings.model_copy(
        update={
            "provider": app.state.service.settings.provider.model_copy(update={"crm_enabled": True})
        }
    )
    return Delivery(settings, app.state.service.sessions)


def contact():
    return {"email": "owner@example.com", "name": "Test owner", "phone": "+15555550123"}


def test_crm_create_requires_matching_readback(app: FastAPI, monkeypatch):
    methods = []

    def response(self, method, url, **kwargs):
        methods.append(method)
        if url.endswith("/search"):
            return httpx.Response(200, json={"results": []})
        properties = {
            "email": contact()["email"],
            "firstname": contact()["name"],
            "phone": contact()["phone"],
        }
        return httpx.Response(200, json={"id": "test-contact", "properties": properties})

    monkeypatch.setattr(httpx.Client, "request", response)
    assert configured(app).crm("test-crm", contact()) == "test-contact"
    assert methods == ["POST", "POST", "GET"]


def test_ambiguous_crm_search_cannot_update_an_arbitrary_match(app, monkeypatch):
    monkeypatch.setattr(
        httpx.Client,
        "request",
        lambda *a, **k: httpx.Response(
            200, json={"results": [{"id": "test-one"}, {"id": "test-two"}]}
        ),
    )
    with pytest.raises(DomainError, match="crm_contact_ambiguous"):
        configured(app).crm("test-crm", contact())


def test_crm_mismatched_receipt_is_not_a_completed_sync(app, monkeypatch):
    def response(self, method, url, **kwargs):
        if url.endswith("/search"):
            return httpx.Response(200, json={"results": []})
        return httpx.Response(
            200, json={"id": "test-contact", "properties": {"email": "other@example.com"}}
        )

    monkeypatch.setattr(httpx.Client, "request", response)
    with pytest.raises(UnknownOutcome, match="crm_receipt"):
        configured(app).crm("test-crm", contact())
