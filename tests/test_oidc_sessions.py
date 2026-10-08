"""Real signed OIDC exchanges through a local-only HTTP issuer and PostgreSQL."""

import hashlib
import json
import secrets
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import pytest
from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient
from joserfc import jwt
from joserfc.jwk import RSAKey
from sqlalchemy import select
from voicebridge.api import create_app
from voicebridge.contracts import DocumentInput
from voicebridge.db import AuthSession, Tenant
from voicebridge.settings import AuthSettings


@pytest.fixture
def issuer() -> Iterator[dict[str, Any]]:
    key = RSAKey.generate_key(2048, parameters={"kid": "test-signing-key"})
    state: dict[str, Any] = {
        "codes": {},
        "subject": "test-owner",
        "email": "owner@example.invalid",
        "bad": None,
    }

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_: Any) -> None:
            return

        def reply(self, value: dict[str, Any], status: int = 200) -> None:
            body = json.dumps(value).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path == "/discovery":
                self.reply(
                    {
                        "issuer": state["url"],
                        "authorization_endpoint": state["url"] + "/authorize",
                        "token_endpoint": state["url"] + "/token",
                        "jwks_uri": state["url"] + "/jwks",
                        "id_token_signing_alg_values_supported": ["RS256"],
                    }
                )
            elif self.path == "/jwks":
                self.reply({"keys": [key.as_dict(private=False)]})
            elif self.path.startswith("/authorize?"):
                params = {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}
                code = secrets.token_urlsafe()
                state["codes"][code] = params
                self.send_response(302)
                self.send_header(
                    "Location",
                    params["redirect_uri"]
                    + "?"
                    + urlencode({"code": code, "state": params["state"]}),
                )
                self.end_headers()
            else:
                self.reply({}, 404)

        def do_POST(self) -> None:
            params = {
                k: v[0]
                for k, v in parse_qs(
                    self.rfile.read(int(self.headers["Content-Length"])).decode()
                ).items()
            }
            saved = state["codes"].pop(params.get("code"), {})
            import base64

            challenge = (
                base64.urlsafe_b64encode(
                    hashlib.sha256(params.get("code_verifier", "").encode()).digest()
                )
                .decode()
                .rstrip("=")
            )
            if (
                not saved
                or saved.get("code_challenge") != challenge
                or saved.get("code_challenge_method") != "S256"
            ):
                self.reply({"error": "invalid_grant"}, 400)
                return
            claims = {
                "iss": state["url"],
                "aud": "test-web-client",
                "sub": state["subject"],
                "email": state["email"],
                "email_verified": True,
                "iat": int(time.time()),
                "exp": int(time.time()) + 60,
                "nonce": saved["nonce"],
            }
            if state["bad"] == "issuer":
                claims["iss"] = "https://untrusted.example.invalid"
            elif state["bad"] == "audience":
                claims["aud"] = "test-wrong-client"
            elif state["bad"] == "expiry":
                claims["exp"] = int(time.time()) - 10
            elif state["bad"] == "nonce":
                claims["nonce"] = "test-wrong-nonce"
            signing = (
                RSAKey.generate_key(2048, parameters={"kid": "test-signing-key"})
                if state["bad"] == "signature"
                else key
            )
            encoded = jwt.encode({"alg": "RS256", "kid": "test-signing-key"}, claims, signing)
            self.reply(
                {"access_token": "test-access-token", "token_type": "Bearer", "id_token": encoded}
            )

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    state["url"] = "http://127.0.0.1:" + str(server.server_port)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def configured(app: FastAPI, issuer: dict[str, Any], tmp_path: Path) -> FastAPI:
    policy = tmp_path / "access.json"
    policy.write_text(
        json.dumps(
            {
                "bindings": [
                    {
                        "issuer": issuer["url"],
                        "verified_email": "owner@example.invalid",
                        "tenant_id": "northline",
                        "role": "owner",
                    },
                    {
                        "issuer": issuer["url"],
                        "subject": "test-viewer",
                        "tenant_id": "northline",
                        "role": "viewer",
                    },
                    {
                        "issuer": issuer["url"],
                        "subject": "test-operator",
                        "tenant_id": "northline",
                        "role": "operator",
                    },
                    {
                        "issuer": issuer["url"],
                        "subject": "test-other",
                        "tenant_id": "test-other-tenant",
                        "role": "owner",
                    },
                ]
            }
        )
    )
    origin = "http://localhost:18080"
    auth = AuthSettings(
        discovery_url=issuer["url"] + "/discovery",
        issuer=issuer["url"],
        client_id="test-web-client",
        client_secret=issuer.get("test_secret", "test-key"),
        redirect_uri=origin + "/auth/callback",
        post_login_uri=origin + "/#/engine",
        scope="openid email",
        algorithms=["RS256"],
        encryption_key=Fernet.generate_key(),
        access_file=policy,
        cookie_name="test-session",
        login_cookie_name="test-login",
        cookie_secure=False,
        session_seconds=3600,
        idle_seconds=600,
        login_seconds=60,
        timeout_seconds=5,
        max_pending_logins=100,
        max_sessions=100,
    )
    settings = app.state.service.settings.model_copy(update={"auth": auth, "origins": [origin]})
    instance = create_app(settings)
    with instance.state.service.sessions.begin() as s:
        s.add(Tenant(id="test-other-tenant", name="Synthetic other tenant"))
    instance.state.service.seed("test-other-tenant")
    return instance


def login(client: TestClient, issuer: dict[str, Any], tamper: bool = False) -> Any:
    import httpx

    start = client.get("/auth/login", follow_redirects=False)
    assert start.status_code == 302, start.text
    authorize = httpx.get(start.headers["location"], follow_redirects=False)
    callback = urlparse(authorize.headers["location"])
    path = callback.path + "?" + callback.query
    if tamper:
        params = parse_qs(callback.query)
        path = (
            callback.path
            + "?"
            + urlencode({"code": params["code"][0], "state": "test-wrong-state"})
        )
    return client.get(path, follow_redirects=False)


def test_login_csrf_logout_and_encrypted_session(
    app: FastAPI, issuer: dict[str, Any], tmp_path: Path
) -> None:
    instance = configured(app, issuer, tmp_path)
    with TestClient(instance) as c:
        assert c.get("/api/state").status_code == 401
        response = login(c, issuer)
        assert response.status_code == 303, response.text
        assert "HttpOnly" in response.headers["set-cookie"]
        status = c.get("/auth/session").json()
        assert status["role"] == "owner"
        assert c.get("/api/state").status_code == 200
        with instance.state.service.sessions() as s:
            rows = list(s.scalars(select(AuthSession)))
            assert len(rows) == 1
            assert "test-owner" not in rows[0].payload
            assert status["csrf"] not in rows[0].payload
        assert c.post("/auth/logout").status_code == 403
        headers = {"Origin": "http://localhost:18080", "X-CSRF-Token": status["csrf"]}
        saved = c.cookies.get("test-session")
        assert c.post("/auth/logout", headers=headers).status_code == 204
        c.cookies.set("test-session", saved)
        assert c.get("/api/state").status_code == 401


@pytest.mark.parametrize("bad", ["issuer", "audience", "expiry", "nonce", "signature", "state"])
def test_invalid_oidc_is_denied(
    app: FastAPI, issuer: dict[str, Any], tmp_path: Path, bad: str
) -> None:
    instance = configured(app, issuer, tmp_path)
    issuer["bad"] = bad
    with TestClient(instance) as c:
        result = login(c, issuer, tamper=bad == "state")
        assert result.status_code == 401
        assert c.get("/api/state").status_code == 401


@pytest.mark.parametrize("role,subject", [("viewer", "test-viewer"), ("operator", "test-operator")])
def test_roles_and_tenant_binding(
    app: FastAPI, issuer: dict[str, Any], tmp_path: Path, role: str, subject: str
) -> None:
    instance = configured(app, issuer, tmp_path)
    issuer.update(subject=subject, email="test-user@example.invalid")
    with TestClient(instance) as c:
        assert login(c, issuer).status_code == 303
        status = c.get("/auth/session").json()
        assert status["role"] == role
        headers = {"Origin": "http://localhost:18080", "X-CSRF-Token": status["csrf"]}
        assert c.post("/api/evaluations", headers=headers).status_code == 403
        assert c.post(
            "/api/knowledge", json={"name": "test", "text": "test"}, headers=headers
        ).status_code == (403 if role == "viewer" else 200)
        instance.state.service.document(
            "test-other-tenant",
            DocumentInput(name="Private other tenant", text="other tenant content"),
        )
        state = c.get("/api/state?tenant=test-other-tenant")
        assert state.status_code == 200
        assert "Private other tenant" not in state.text
        assert c.post("/auth/logout", headers=headers).status_code == 204


def test_email_binding_cannot_reassign_subject(
    app: FastAPI, issuer: dict[str, Any], tmp_path: Path
) -> None:
    instance = configured(app, issuer, tmp_path)
    with TestClient(instance) as c:
        assert login(c, issuer).status_code == 303
    issuer["subject"] = "test-reassigned-subject"
    with TestClient(instance) as c:
        assert login(c, issuer).status_code == 403


def test_expiry_idle_tampering_and_callback_replay(
    app: FastAPI, issuer: dict[str, Any], tmp_path: Path
) -> None:
    from datetime import timedelta
    from urllib.parse import urlparse

    import httpx
    from voicebridge.db import now

    instance = configured(app, issuer, tmp_path)
    with TestClient(instance) as c:
        start = c.get("/auth/login", follow_redirects=False)
        authorize = httpx.get(start.headers["location"], follow_redirects=False)
        path = urlparse(authorize.headers["location"])
        callback = path.path + "?" + path.query
        cookie = c.cookies.get("test-login")
        assert c.get(callback, follow_redirects=False).status_code == 303
        c.cookies.set("test-login", cookie)
        assert c.get(callback, follow_redirects=False).status_code == 401
        with instance.state.service.sessions.begin() as s:
            row = s.scalar(select(AuthSession))
            assert row is not None
            row.last_seen = now() - timedelta(seconds=601)
        assert c.get("/auth/session").status_code == 401
        # Remove the manually injected duplicate-domain replay cookie before a fresh login.
        c.cookies.clear()
        assert login(c, issuer).status_code == 303
        with instance.state.service.sessions.begin() as s:
            row = s.scalar(select(AuthSession))
            assert row is not None
            row.expires = now() - timedelta(seconds=1)
        assert c.get("/api/state").status_code == 401


def test_pending_capacity_is_separate_and_idle_sessions_are_reclaimed(
    app: FastAPI, issuer: dict[str, Any], tmp_path: Path
) -> None:
    from datetime import timedelta

    from voicebridge.db import now

    instance = configured(app, issuer, tmp_path)
    config = instance.state.authentication.config
    config.max_pending_logins = 1
    with TestClient(instance) as c:
        assert login(c, issuer).status_code == 303
        # An authenticated session must not consume the pending-login quota.
        assert c.get("/auth/login", follow_redirects=False).status_code == 302
        with instance.state.service.sessions.begin() as s:
            rows = list(s.scalars(select(AuthSession)))
            assert len(rows) == 2
            assert {r.kind for r in rows} == {"login", "session"}
            for row in rows:
                row.last_seen = now() - timedelta(seconds=601)
        assert c.get("/auth/login", follow_redirects=False).status_code == 302
        with instance.state.service.sessions() as s:
            rows = list(s.scalars(select(AuthSession)))
            assert len(rows) == 1
            assert rows[0].kind == "login"
        c.cookies.set("test-session", "test-forged-cookie")
        assert c.get("/api/state").status_code == 401
