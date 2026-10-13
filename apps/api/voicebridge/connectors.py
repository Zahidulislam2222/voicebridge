"""Replaceable calendar/CRM transports and local capture; execution is explicit."""

import hashlib
import re
import smtplib
import ssl
from contextlib import nullcontext
from email.message import EmailMessage
from email.utils import formataddr
from typing import Any, Literal, Protocol
from urllib.parse import quote, unquote, urlparse

import httpx
from sqlalchemy import DateTime, cast, select
from sqlalchemy.orm import Session, sessionmaker

from .contracts import DomainError
from .db import ExternalRecord, tenant_lock
from .protocol import SINGLE_EMAIL_PATTERN
from .settings import FollowupTemplate, Settings, read_data


class UnknownOutcome(Exception):
    """A side effect may have happened; never retry it blindly."""


class RetryableFailure(Exception):
    """A known pre-send failure may be retried."""


class Calendar(Protocol):
    def get(self, key: str) -> dict[str, Any] | None: ...
    def put(self, key: str, payload: dict[str, Any]) -> str: ...
    def available(
        self, start: str, end: str, exclude: str | None = None, session: Session | None = None
    ) -> bool: ...


class LocalCalendar:
    def __init__(self, sessions: sessionmaker[Session], kind: str) -> None:
        self.sessions = sessions
        self.kind = kind
        self.fail_before = False
        self.timeout_after_write = False

    def get(self, key: str) -> dict[str, Any] | None:
        with self.sessions() as session:
            row = session.get(ExternalRecord, key)
            return row.value if row and row.kind == self.kind else None

    def put(self, key: str, payload: dict[str, Any]) -> str:
        if self.fail_before:
            raise RetryableFailure("calendar_unavailable")
        with self.sessions.begin() as session:
            tenant_lock(session, "local-calendar-" + key)
            row = session.get(ExternalRecord, key)
            if row:
                if row.kind != self.kind:
                    raise DomainError("calendar_scope_mismatch", 403)
                if int(row.value["revision"]) > int(payload["revision"]):
                    raise DomainError("calendar_revision_superseded")
                row.value = payload
            else:
                session.add(ExternalRecord(id=key, kind=self.kind, value=payload))
        if self.timeout_after_write:
            raise UnknownOutcome("calendar_write_unverified")
        return key

    def available(
        self, start: str, end: str, exclude: str | None = None, session: Session | None = None
    ) -> bool:
        from contextlib import nullcontext
        from datetime import datetime

        with nullcontext(session) if session else self.sessions() as active:
            query = select(ExternalRecord.id).where(
                ExternalRecord.kind == self.kind,
                ExternalRecord.value["status"].as_string() != "cancelled",
                cast(ExternalRecord.value["start"].as_string(), DateTime(timezone=True))
                < datetime.fromisoformat(end),
                cast(ExternalRecord.value["end"].as_string(), DateTime(timezone=True))
                > datetime.fromisoformat(start),
            )
            if exclude:
                query = query.where(ExternalRecord.id != exclude)
            return active.scalar(query.limit(1)) is None


class RemoteTransport:
    def __init__(self, settings: Settings, scope: Literal["calendar", "crm", "voice"]) -> None:
        self.settings = settings
        self.scope = scope

    def request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any] | None = None,
        *,
        allow_absent: bool = False,
    ) -> dict[str, Any]:
        provider = self.settings.provider
        if not getattr(provider, self.scope + "_enabled"):
            raise DomainError("external_execution_disabled", 403)
        destinations = {
            "calendar": (
                provider.base_url.rstrip("/")
                + provider.calendar_path.format(calendar_id=quote(provider.calendar_id, safe="")),
            ),
            "crm": (provider.contacts_path,),
            "voice": (
                provider.retell_base_url,
                provider.vapi_base_url,
                provider.elevenlabs_base_url,
            ),
        }
        requested = urlparse(url)
        unsafe_path = any(
            unquote(part) in {".", ".."}
            or any(char in unquote(part) for char in ("/", "\\", "%", ";"))
            for part in requested.path.split("/")
        )
        if (
            requested.username
            or requested.password
            or requested.fragment
            or requested.params
            or unsafe_path
            or not any(
                requested.scheme == allowed.scheme
                and requested.netloc == allowed.netloc
                and (
                    requested.path == allowed.path.rstrip("/")
                    or requested.path.startswith(allowed.path.rstrip("/") + "/")
                )
                for allowed in map(urlparse, destinations[self.scope])
            )
        ):
            raise DomainError("connector_destination_denied", 403)
        if (
            urlparse(url).hostname == urlparse(self.settings.provider.vapi_base_url).hostname
            and not self.settings.provider.vapi_owner_resolved
        ):
            raise DomainError("vapi_owner_resolution_required", 403)
        try:
            with httpx.Client(
                timeout=self.settings.provider.timeout_seconds,
                follow_redirects=False,
                trust_env=False,
            ) as client:
                response = client.request(
                    method,
                    url,
                    headers={**headers, "User-Agent": self.settings.provider.user_agent},
                    json=payload,
                )
        except httpx.TransportError as exc:
            raise UnknownOutcome("external_result_unverified") from exc
        if allow_absent and response.status_code == 404 and method in {"GET", "DELETE"}:
            return {"missing": True}
        if allow_absent and response.status_code == 410 and method == "DELETE":
            try:
                error = response.json()
            except ValueError as exc:
                raise UnknownOutcome("connector_receipt_invalid") from exc
            details = error.get("error") if isinstance(error, dict) else None
            errors = details.get("errors") if isinstance(details, dict) else None
            if isinstance(errors, list) and any(
                isinstance(item, dict) and item.get("reason") == "deleted" for item in errors
            ):
                return {"missing": True}
        if response.status_code in {401, 403}:
            raise DomainError("connector_authorization_denied", 403)
        if response.status_code >= 400:
            # Never include provider bodies, URLs, credentials or customer data in errors.
            raise DomainError("connector_rejected")
        if response.status_code == 204:
            return {}
        try:
            value: object = response.json()
        except ValueError as exc:
            raise UnknownOutcome("connector_receipt_invalid") from exc
        if not isinstance(value, dict):
            raise DomainError("connector_invalid_response", 502)
        return value


class GoogleCalendar:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.transport = RemoteTransport(settings, "calendar")

    def headers(self) -> dict[str, str]:
        p = self.settings.provider
        if not p.calendar_enabled:
            raise DomainError("external_execution_disabled", 403)
        try:
            with httpx.Client(timeout=p.timeout_seconds, trust_env=False) as client:
                r = client.post(
                    p.token_url,
                    data={
                        "grant_type": "refresh_token",
                        "client_id": p.google_client_id,
                        "client_secret": p.google_client_secret.get_secret_value(),
                        "refresh_token": p.google_refresh_token.get_secret_value(),
                    },
                )
        except httpx.TransportError as exc:
            raise RetryableFailure("oauth_unavailable") from exc
        if r.status_code != 200:
            raise DomainError("oauth_revoked_or_scope_missing", 403)
        try:
            value = r.json()
        except ValueError as exc:
            raise RetryableFailure("oauth_invalid_response") from exc
        token = value.get("access_token") if isinstance(value, dict) else None
        if not isinstance(token, str) or not token.strip():
            raise RetryableFailure("oauth_invalid_response")
        return {"Authorization": "Bearer " + token}

    def url(self, key: str | None = None) -> str:
        p = self.settings.provider
        path = p.calendar_path.format(calendar_id=quote(p.calendar_id, safe=""))
        return p.base_url.rstrip("/") + path + ("/" + quote(key, safe="") if key else "")

    def get(self, key: str) -> dict[str, Any] | None:
        data = self.transport.request("GET", self.url(key), self.headers(), allow_absent=True)
        if data.get("missing"):
            # Event404 can also mean its calendar is inaccessible; verify the
            # collection before interpreting it as an absent event.
            self.transport.request("GET", self.url() + "?maxResults=1", self.headers())
            return None
        if data.get("status") == "cancelled":
            return {"status": "cancelled", "etag": data.get("etag")}
        return {
            "start": data["start"]["dateTime"],
            "end": data["end"]["dateTime"],
            "status": "confirmed",
            "revision": data.get("extendedProperties", {}).get("private", {}).get("revision"),
            "etag": data.get("etag"),
        }

    def put(self, key: str, payload: dict[str, Any]) -> str:
        existing = self.get(key)
        headers = self.headers()
        if existing:
            if existing.get("revision") is not None and int(existing["revision"]) > int(
                payload["revision"]
            ):
                raise DomainError("calendar_revision_superseded")
            if not existing.get("etag"):
                raise DomainError("calendar_version_missing")
            headers["If-Match"] = existing["etag"]
        if payload["status"] == "cancelled":
            self.transport.request("DELETE", self.url(key), headers, allow_absent=True)
            return key
        data = {
            "id": key,
            "summary": payload["service"],
            "start": {"dateTime": payload["start"]},
            "end": {"dateTime": payload["end"]},
            "extendedProperties": {"private": {"revision": str(payload["revision"])}},
        }
        if existing:
            receipt = self.transport.request("PUT", self.url(key), headers, data)
        else:
            receipt = self.transport.request("POST", self.url(), headers, data)
        if receipt.get("id") != key or receipt.get("status") == "cancelled":
            raise UnknownOutcome("calendar_receipt_invalid")
        return key

    def available(
        self, start: str, end: str, exclude: str | None = None, session: Session | None = None
    ) -> bool:
        # Query the approved calendar's event list, never primary/global calendars.
        from urllib.parse import urlencode

        url = (
            self.url() + "?" + urlencode({"timeMin": start, "timeMax": end, "singleEvents": "true"})
        )
        data = self.transport.request("GET", url, self.headers())
        if data.get("nextPageToken"):
            raise DomainError("calendar_availability_incomplete", 503)
        return not any(
            item.get("id") != exclude
            and item.get("status") != "cancelled"
            and item.get("transparency") != "transparent"
            for item in data.get("items", [])
        )


class Delivery:
    def __init__(self, settings: Settings, sessions: sessionmaker[Session]) -> None:
        self.settings, self.sessions = settings, sessions

    def crm(self, key: str, payload: dict[str, Any], session: Session | None = None) -> str:
        p = self.settings.provider
        if p.crm_enabled:
            # Search by email first; reconcile ambiguous create instead of duplicate POST.
            transport = RemoteTransport(self.settings, "crm")
            headers = {"Authorization": "Bearer " + p.hubspot_key.get_secret_value()}
            search = transport.request(
                "POST",
                p.contacts_path + "/search",
                headers,
                {
                    "filterGroups": [
                        {
                            "filters": [
                                {
                                    "propertyName": "email",
                                    "operator": "EQ",
                                    "value": payload["email"],
                                }
                            ]
                        }
                    ]
                },
            )
            matches = search.get("results")
            if not isinstance(matches, list):
                raise DomainError("crm_invalid_search_receipt", 502)
            if len(matches) > 1:
                raise DomainError("crm_contact_ambiguous", 409)
            properties = {
                "email": payload["email"],
                "firstname": payload["name"],
                "phone": payload["phone"],
            }
            if matches:
                existing_id = matches[0].get("id") if isinstance(matches[0], dict) else None
                if not isinstance(existing_id, str) or not existing_id.strip():
                    raise DomainError("crm_invalid_search_receipt", 502)
                result = transport.request(
                    "PATCH",
                    p.contacts_path + "/" + quote(existing_id, safe=""),
                    headers,
                    {"properties": properties},
                )
                if result.get("id") != existing_id:
                    raise UnknownOutcome("crm_receipt_mismatch")
            else:
                result = transport.request(
                    "POST", p.contacts_path, headers, {"properties": properties}
                )
            receipt = result.get("id")
            if not isinstance(receipt, str) or not receipt.strip():
                raise UnknownOutcome("crm_receipt_missing")
            readback = transport.request(
                "GET",
                p.contacts_path
                + "/"
                + quote(receipt, safe="")
                + "?properties=email,firstname,phone",
                headers,
            )
            actual = readback.get("properties")
            if (
                readback.get("id") != receipt
                or not isinstance(actual, dict)
                or any(actual.get(name) != value for name, value in properties.items())
            ):
                raise UnknownOutcome("crm_receipt_mismatch")
            return receipt
        with nullcontext(session) if session else self.sessions.begin() as active:
            row = active.get(ExternalRecord, key)
            if row:
                row.value = payload
            else:
                active.add(ExternalRecord(id=key, kind="crm", value=payload))
        return key

    def followup(self, key: str, payload: dict[str, Any]) -> str:
        email = payload.get("email")
        if self.settings.followup_transport == "smtp":
            if not self.settings.external_delivery_enabled:
                raise DomainError("external_delivery_disabled", 403)
            if (
                not isinstance(email, str)
                or not re.fullmatch(SINGLE_EMAIL_PATTERN, email)
                or email.lower() not in {a.lower() for a in self.settings.followup_recipients}
            ):
                raise DomainError("recipient_not_authorized", 403)
        elif (
            not isinstance(email, str)
            or not re.fullmatch(SINGLE_EMAIL_PATTERN, email)
            or not email.lower().endswith(".invalid")
        ):
            raise DomainError("synthetic_recipient_required", 403)
        template = FollowupTemplate.model_validate(read_data(self.settings.template_file))
        body = template.body.format(**payload)
        if self.settings.followup_transport == "n8n":
            try:
                with httpx.Client(timeout=self.settings.smtp_timeout_seconds, trust_env=False) as c:
                    r = c.post(
                        self.settings.n8n_url,
                        headers={
                            "Authorization": "Bearer " + self.settings.n8n_key.get_secret_value()
                        },
                        json={
                            "operation_key": key,
                            "email": payload["email"],
                            "subject": template.subject,
                            "body": body,
                        },
                    )
            except httpx.TransportError as exc:
                raise UnknownOutcome("followup_unverified") from exc
            if r.status_code != 200:
                raise UnknownOutcome("followup_unverified")
            try:
                outcome = r.json()
            except ValueError as exc:
                raise UnknownOutcome("followup_receipt_invalid") from exc
            if (
                not isinstance(outcome, dict)
                or outcome.get("operation_key") != key
                or outcome.get("accepted") is not True
                or not isinstance(outcome.get("receipt"), str)
                or not outcome["receipt"].strip()
            ):
                raise UnknownOutcome("followup_receipt_missing")
            return str(outcome["receipt"])
        msg = EmailMessage()
        msg["From"] = formataddr((template.from_name, self.settings.smtp_from))
        msg["To"] = payload["email"]
        msg["Subject"] = template.subject
        msg["Message-ID"] = (
            "<"
            + hashlib.sha256(key.encode()).hexdigest()
            + "@"
            + self.settings.smtp_from.rsplit("@", 1)[-1]
            + ">"
        )
        msg.set_content(body)
        if self.settings.followup_transport == "smtp":
            return self.authenticated_smtp(key, msg)
        try:
            with smtplib.SMTP(
                self.settings.smtp_host,
                self.settings.smtp_port,
                timeout=self.settings.smtp_timeout_seconds,
            ) as smtp:
                smtp.send_message(msg)
        except OSError as exc:
            raise UnknownOutcome("followup_unverified") from exc
        return key

    def authenticated_smtp(self, key: str, message: EmailMessage) -> str:
        settings = self.settings
        context = ssl.create_default_context()
        started = accepted = False
        try:
            connection = (
                smtplib.SMTP_SSL(
                    settings.smtp_host,
                    settings.smtp_port,
                    timeout=settings.smtp_timeout_seconds,
                    context=context,
                )
                if settings.smtp_security == "tls"
                else smtplib.SMTP(
                    settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout_seconds
                )
            )
            with connection as smtp:
                if settings.smtp_security == "starttls":
                    smtp.ehlo()
                    smtp.starttls(context=context)
                    smtp.ehlo()
                smtp.login(settings.smtp_username, settings.smtp_password.get_secret_value())
                started = True
                if smtp.send_message(message):
                    raise DomainError("followup_recipient_refused", 422)
                accepted = True
        except smtplib.SMTPAuthenticationError as exc:
            raise DomainError("followup_authorization_denied", 403) from exc
        except smtplib.SMTPRecipientsRefused as exc:
            raise DomainError("followup_recipient_refused", 422) from exc
        except smtplib.SMTPResponseException as exc:
            if not accepted:
                if 400 <= exc.smtp_code < 500:
                    raise RetryableFailure("smtp_temporarily_rejected") from exc
                raise DomainError("followup_rejected", 422) from exc
        except OSError as exc:
            if not accepted:
                if started:
                    raise UnknownOutcome("followup_unverified") from exc
                raise RetryableFailure("smtp_connection_unavailable") from exc
        # SMTP acceptance proves the receiving relay accepted the message,
        # not that it reached the recipient's inbox. Keep the stable identity.
        return key
