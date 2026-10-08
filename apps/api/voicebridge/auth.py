"""Maintained OIDC client with encrypted, opaque, revocable PostgreSQL sessions."""

import hashlib
import hmac
import json
import secrets
from datetime import timedelta
from typing import Any
from urllib.parse import urlparse

from authlib.integrations.starlette_client import OAuth
from cryptography.fernet import Fernet, InvalidToken
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session, sessionmaker

from .contracts import DomainError
from .db import AuthSession, Record, Tenant, now, tenant_lock
from .protocol import OWNER_API_PREFIXES, SAFE_HTTP_METHODS
from .settings import AccessPolicy, Settings


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class Authentication:
    def __init__(self, settings: Settings, sessions: sessionmaker[Session]):
        self.settings, self.sessions = settings, sessions
        self.config = settings.auth
        self.client: Any = None
        if self.config:
            self.cipher = Fernet(self.config.encryption_key.get_secret_value().encode())
            oauth = OAuth()
            self.client = oauth.register(
                "identity",
                client_id=self.config.client_id,
                client_secret=self.config.client_secret.get_secret_value(),
                server_metadata_url=self.config.discovery_url,
                client_kwargs={
                    "scope": self.config.scope,
                    "code_challenge_method": "S256",
                    "timeout": self.config.timeout_seconds,
                    "trust_env": False,
                },
            )

    def encode(self, value: dict[str, Any]) -> str:
        return self.cipher.encrypt(json.dumps(value).encode()).decode()

    def decode(self, value: str) -> dict[str, Any]:
        result: Any = json.loads(self.cipher.decrypt(value.encode()))
        if not isinstance(result, dict):
            raise DomainError("authorization_required", 401)
        return dict(result)

    def policy(self) -> AccessPolicy:
        if self.config is None:
            raise DomainError("authorization_required", 401)
        return AccessPolicy.model_validate_json(self.config.access_file.read_text())

    def grant(self, claims: dict[str, Any]) -> dict[str, str]:
        """Subject pinning prevents an email bootstrap from silently rebinding later."""
        issuer, subject = claims.get("iss"), claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise DomainError("identity_not_allowed", 403)
        for binding in self.policy().bindings:
            if issuer != binding.issuer:
                continue
            if binding.subject:
                match = hmac.compare_digest(subject, binding.subject)
            else:
                match = (
                    claims.get("email_verified") is True
                    and isinstance(claims.get("email"), str)
                    and claims["email"].casefold() == str(binding.verified_email).casefold()
                )
            if not match:
                continue
            with self.sessions.begin() as s:
                if not s.get(Tenant, binding.tenant_id):
                    raise DomainError("identity_not_allowed", 403)
                if binding.verified_email:
                    tenant_lock(s, binding.tenant_id)
                    key = digest(binding.issuer + "\n" + binding.verified_email.casefold())
                    row = s.scalar(
                        select(Record).where(
                            Record.tenant_id == binding.tenant_id,
                            Record.kind == "identity_binding",
                            Record.key == key,
                        )
                    )
                    if row and row.value.get("subject") != subject:
                        raise DomainError("identity_not_allowed", 403)
                    if not row:
                        s.add(
                            Record(
                                id=secrets.token_hex(),
                                tenant_id=binding.tenant_id,
                                kind="identity_binding",
                                key=key,
                                value={"subject": subject},
                            )
                        )
            return {"tenant": binding.tenant_id, "role": binding.role, "subject": subject}
        raise DomainError("identity_not_allowed", 403)

    def load(self, token: str, *, consume: bool = False) -> dict[str, Any]:
        if not self.config or not token or len(token) > 256:
            raise DomainError("authorization_required", 401)
        with self.sessions.begin() as s:
            row = s.scalar(
                select(AuthSession).where(AuthSession.digest == digest(token)).with_for_update()
            )
            if not row:
                raise DomainError("authorization_required", 401)
            if (
                row.expires <= now()
                or row.last_seen + timedelta(seconds=self.config.idle_seconds) <= now()
            ):
                s.delete(row)
                expired = True
                payload = {}
            else:
                expired = False
                try:
                    payload = self.decode(row.payload)
                except (InvalidToken, ValueError):
                    raise DomainError("authorization_required", 401) from None
                if consume:
                    s.delete(row)
                else:
                    row.last_seen = now()
        if expired:
            raise DomainError("session_expired", 401)
        return payload

    def save(self, payload: dict[str, Any], tenant: str, seconds: int) -> str:
        if self.config is None:
            raise DomainError("authorization_required", 401)
        token = secrets.token_urlsafe(32)
        kind = payload["kind"]
        if kind not in {"login", "session"}:
            raise DomainError("invalid_session", 401)
        with self.sessions.begin() as s:
            tenant_lock(s, self.settings.tenant_id)
            s.execute(
                delete(AuthSession).where(
                    or_(
                        AuthSession.expires <= now(),
                        AuthSession.last_seen
                        <= now() - timedelta(seconds=self.config.idle_seconds),
                    )
                )
            )
            count = (
                s.scalar(
                    select(func.count()).select_from(AuthSession).where(AuthSession.kind == kind)
                )
                or 0
            )
            limit = self.config.max_pending_logins if kind == "login" else self.config.max_sessions
            if count >= limit:
                raise DomainError("login_capacity", 429)
            s.add(
                AuthSession(
                    digest=digest(token),
                    kind=kind,
                    tenant_id=tenant,
                    payload=self.encode(payload),
                    expires=now() + timedelta(seconds=seconds),
                    last_seen=now(),
                )
            )
        return token

    def revoke(self, token: str) -> None:
        with self.sessions.begin() as s:
            s.execute(delete(AuthSession).where(AuthSession.digest == digest(token)))

    def authorize(self, request: Request) -> str:
        if self.config is None:
            raise DomainError("authorization_required", 401)
        payload = self.load(request.cookies.get(self.config.cookie_name, ""))
        if payload.get("kind") != "session":
            raise DomainError("authorization_required", 401)
        granted = self.grant(payload["identity"])
        if granted["tenant"] != payload["tenant"]:
            raise DomainError("identity_not_allowed", 403)
        if request.method not in SAFE_HTTP_METHODS:
            if request.headers.get("origin") not in self.settings.origins:
                raise DomainError("untrusted_origin", 403)
            if not hmac.compare_digest(request.headers.get("x-csrf-token", ""), payload["csrf"]):
                raise DomainError("csrf_required", 403)
            if granted["role"] == "viewer":
                raise DomainError("role_denied", 403)
            if granted["role"] != "owner" and request.url.path.startswith(OWNER_API_PREFIXES):
                raise DomainError("role_denied", 403)
        request.state.identity = granted
        return granted["tenant"]

    async def metadata(self) -> None:
        if self.config is None:
            raise DomainError("authorization_required", 401)
        metadata = await self.client.load_server_metadata()
        if metadata.get("issuer") != self.config.issuer:
            raise DomainError("invalid_identity_provider", 503)
        for field in ("authorization_endpoint", "token_endpoint", "jwks_uri"):
            parsed = urlparse(metadata.get(field, ""))
            if (
                not parsed.hostname
                or parsed.username
                or parsed.password
                or (
                    parsed.scheme != "https"
                    and not (
                        not self.config.cookie_secure
                        and parsed.scheme == "http"
                        and parsed.hostname in {"127.0.0.1", "localhost", "::1"}
                    )
                )
            ):
                raise DomainError("invalid_identity_provider", 503)
        metadata["id_token_signing_alg_values_supported"] = self.config.algorithms

    def install(self, app: FastAPI) -> None:
        if not self.config:
            return
        config = self.config

        @app.get("/auth/login")
        async def login(request: Request) -> RedirectResponse:
            request.scope["session"] = {}
            try:
                await self.metadata()
                response = await self.client.authorize_redirect(request, config.redirect_uri)
            except DomainError:
                raise
            except Exception:
                raise DomainError("identity_provider_unavailable", 503) from None
            old = request.cookies.get(config.login_cookie_name)
            if old:
                self.revoke(old)
            token = self.save(
                {"kind": "login", "oauth": request.session},
                self.settings.tenant_id,
                config.login_seconds,
            )
            response.set_cookie(
                config.login_cookie_name,
                token,
                max_age=config.login_seconds,
                secure=config.cookie_secure,
                httponly=True,
                samesite="lax",
            )
            return response  # type: ignore[no-any-return]

        @app.get("/auth/callback")
        async def callback(request: Request) -> RedirectResponse:
            payload = self.load(request.cookies.get(config.login_cookie_name, ""), consume=True)
            if payload.get("kind") != "login":
                raise DomainError("invalid_login", 401)
            request.scope["session"] = payload["oauth"]
            state = request.query_params.get("state", "")
            saved = payload["oauth"].get("_state_identity_" + state, {})
            nonce = saved.get("data", {}).get("nonce")
            try:
                await self.metadata()
                token = await self.client.authorize_access_token(
                    request, claims_options={"iss": {"values": [config.issuer]}}, leeway=0
                )
                claims = dict(token.get("userinfo") or {})
                # Authlib supports providers which waive nonce; this application does not.
                if not nonce or claims.get("nonce") != nonce:
                    raise DomainError("invalid_login", 401)
                granted = self.grant(claims)
            except DomainError:
                raise
            except Exception:
                raise DomainError("invalid_login", 401) from None
            old = request.cookies.get(config.cookie_name)
            if old:
                self.revoke(old)
            session = self.save(
                {
                    "kind": "session",
                    "tenant": granted["tenant"],
                    "identity": {
                        k: claims[k]
                        for k in ("iss", "sub", "email", "email_verified")
                        if k in claims
                    },
                    "csrf": secrets.token_urlsafe(32),
                },
                granted["tenant"],
                config.session_seconds,
            )
            response = RedirectResponse(config.post_login_uri, status_code=303)
            response.delete_cookie(
                config.login_cookie_name, secure=config.cookie_secure, httponly=True
            )
            response.set_cookie(
                config.cookie_name,
                session,
                max_age=config.session_seconds,
                secure=config.cookie_secure,
                httponly=True,
                samesite="lax",
            )
            return response

        @app.get("/auth/session")
        def session(request: Request) -> dict[str, Any]:
            tenant = self.authorize(request)
            payload = self.load(request.cookies[config.cookie_name])
            return {
                "authenticated": True,
                "tenant": tenant,
                "role": request.state.identity["role"],
                "csrf": payload["csrf"],
            }

        @app.post("/auth/logout", status_code=204)
        def logout(request: Request) -> JSONResponse:
            # Viewer logout is a permitted session mutation, not a business operation.
            payload = self.load(request.cookies.get(config.cookie_name, ""))
            if (
                payload.get("kind") != "session"
                or request.headers.get("origin") not in self.settings.origins
            ):
                raise DomainError("untrusted_origin", 403)
            if not hmac.compare_digest(request.headers.get("x-csrf-token", ""), payload["csrf"]):
                raise DomainError("csrf_required", 403)
            self.revoke(request.cookies[config.cookie_name])
            response = JSONResponse(None, status_code=204)
            response.delete_cookie(config.cookie_name, secure=config.cookie_secure, httponly=True)
            return response
