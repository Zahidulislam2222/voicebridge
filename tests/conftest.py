"""Isolated real PostgreSQL tests; public/provider sockets are forbidden."""

import socket
import uuid
from collections.abc import Iterator
from typing import Any

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from pydantic import SecretStr
from sqlalchemy.engine import make_url
from voicebridge.api import create_app
from voicebridge.settings import load_settings


@pytest.fixture(autouse=True)
def no_external_network(monkeypatch: pytest.MonkeyPatch) -> None:
    connect = socket.socket.connect

    def local_only(self: socket.socket, address: Any) -> Any:
        if isinstance(address, tuple) and address[0] not in {"127.0.0.1", "::1", "localhost"}:
            raise RuntimeError("Tests refuse real provider network access")
        return connect(self, address)

    monkeypatch.setattr(socket.socket, "connect", local_only)


@pytest.fixture
def app() -> Iterator[FastAPI]:
    settings = load_settings(".local/core-engine/.env")
    assert not settings.provider.enabled, "Tests refuse enabled real providers"
    settings = settings.model_copy(
        update={
            "operator_key": SecretStr("test-operator-credential-local-only"),
            "business_key": SecretStr("test-business-credential-local-only"),
            "management_key": SecretStr("test-management-credential-local-only"),
            "business_read_key": SecretStr("test-business-read-credential-local-only"),
            "management_read_key": SecretStr("test-management-read-credential-local-only"),
            "retell_webhook_key": SecretStr("test-key"),
            "vapi_webhook_key": SecretStr("test-key"),
            "n8n_key": SecretStr("test-key"),
            "followup_transport": "capture",
            "provider": settings.provider.model_copy(
                update={
                    "calendar_id": "test-calendar",
                    "vapi_owner_resolved": False,
                    "google_client_id": "test-client",
                    "google_client_secret": SecretStr("test-key"),
                    "google_refresh_token": SecretStr("test-key"),
                    "hubspot_key": SecretStr("test-key"),
                    "retell_key": SecretStr("test-key"),
                    "vapi_key": SecretStr("test-key"),
                    "elevenlabs_key": SecretStr("test-key"),
                }
            ),
        }
    )
    url = make_url(settings.database_url.get_secret_value())
    name = "voicebridge_test_" + uuid.uuid4().hex
    admin_url = url.set(drivername="postgresql", database="postgres")
    with psycopg.connect(admin_url.render_as_string(hide_password=False), autocommit=True) as c:
        c.execute(psycopg.sql.SQL("CREATE DATABASE {}").format(psycopg.sql.Identifier(name)))
    settings = settings.model_copy(
        update={"database_url": url.set(database=name).render_as_string(hide_password=False)}
    )
    # Revalidate SecretStr after constructing the isolated URL.
    settings = type(settings).model_validate(settings.model_dump())
    config = Config(str(settings.migration_config))
    config.attributes["settings"] = settings
    command.upgrade(config, "head")
    instance = create_app(settings)
    instance.state.service.seed(settings.tenant_id)
    try:
        yield instance
    finally:
        instance.state.service.sessions.kw["bind"].dispose()
        with psycopg.connect(admin_url.render_as_string(hide_password=False), autocommit=True) as c:
            c.execute(
                psycopg.sql.SQL("DROP DATABASE {} WITH (FORCE)").format(
                    psycopg.sql.Identifier(name)
                )
            )
