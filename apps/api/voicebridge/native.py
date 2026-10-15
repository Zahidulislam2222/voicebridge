"""Owner-only, crash-aware creation of bounded native web calls."""

import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlparse

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select

from .connectors import RemoteTransport
from .contracts import CallIntentBinding, DomainError, NativeCallInput
from .db import Call, Operation, now, tenant_lock
from .protocol import (
    BUSINESS_TOOLS,
    CALL_CAPABILITY_HEADER,
    CALL_CAPABILITY_METADATA_KEY,
    NATIVE_ACCOUNT_LOCK,
    NATIVE_CALL_READ_PATHS,
    NATIVE_CREATE_PATHS,
    NATIVE_OPERATION_METADATA_KEY,
    NATIVE_OPERATION_PREFIX,
    NATIVE_TERMINAL_STATUSES,
    VAPI_EVENT_PATH,
    VAPI_REQUIRED_SERVER_MESSAGES,
    VAPI_TOOL_PATH,
)
from .providers import Providers
from .service import Service, audit, identity


class NativeCalls:
    def __init__(self, service: Service, providers: Providers) -> None:
        self.service, self.providers = service, providers
        self.settings = service.settings
        self.transport = RemoteTransport(self.settings, "voice")
        self.reconciliation_transport = RemoteTransport(self.settings, "voice_read")

    def _cipher(self) -> Fernet:
        try:
            return Fernet(self.settings.native_cipher_key.get_secret_value().encode())
        except (ValueError, TypeError) as exc:
            raise DomainError("native_secret_unavailable", 503) from exc

    def _seal(self, value: Any) -> str:
        return self._cipher().encrypt(json.dumps(value).encode()).decode()

    def _open(self, value: str) -> Any:
        try:
            return json.loads(self._cipher().decrypt(value.encode()))
        except (InvalidToken, ValueError, TypeError) as exc:
            raise DomainError("native_recovery_unavailable", 503) from exc

    def _entitlement_status(self, provider: str) -> dict[str, str | None]:
        path = self.settings.native_entitlement_file
        if not path:
            return {"state": "unverified", "verified_at": None}
        try:
            data = json.loads(path.read_text())
            verified = datetime.fromisoformat(data["verified_at"])
            detail = data[provider]
            fresh = verified.tzinfo is not None and timedelta(0) <= now() - verified <= timedelta(
                seconds=self.settings.native_entitlement_ttl_seconds
            )
            allowed = (
                fresh
                and detail["prepaid_balance_usd"] > 0
                and detail["recharge_off"] is True
                and detail["billable_addons_usd"] == 0
                and detail["byok_count"] == 0
                and (provider != "vapi" or detail["card_absent"] is True)
            )
        except (OSError, ValueError, KeyError, TypeError, OverflowError):
            allowed = False
            verified = None
        return {
            "state": "verified" if allowed else "stale_or_unverified",
            "verified_at": verified.isoformat() if verified and verified.tzinfo else None,
        }

    def _entitlement(self, provider: str) -> None:
        if self._entitlement_status(provider)["state"] != "verified":
            raise DomainError("native_free_entitlement_unverified", 403)

    def status(self, tenant: str, owner: str) -> dict[str, Any]:
        """Expose only recovery metadata for the authenticated owner, never grants or keys."""
        owner_digest = hashlib.sha256(owner.encode()).hexdigest()
        with self.service.sessions() as session:
            rows = session.scalars(
                select(Operation)
                .where(
                    Operation.tenant_id == tenant,
                    Operation.key.like(NATIVE_OPERATION_PREFIX + "%"),
                    Operation.result["owner"].as_string() == owner_digest,
                )
                .order_by(Operation.result["created_at"].as_string().desc())
                .limit(self.settings.max_records_per_page)
            ).all()
            operations = []
            for row in rows:
                data = row.result
                state = str(data.get("state", "UNKNOWN"))
                recovery = "none"
                if state == "BOUND":
                    call = session.get(Call, data.get("intent_id"))
                    if call and call.state == "ended":
                        state = "DONE"
                    else:
                        try:
                            self._checked_bound_grant(row, call)
                            recovery = "resume_existing_call"
                        except (DomainError, KeyError, TypeError, ValueError):
                            recovery = "manual_reconciliation_required"
                elif state in {"RESERVED", "REQUEST_PENDING", "UNKNOWN", "EXTERNAL_CREATED"}:
                    recovery = "manual_reconciliation_required"
                operations.append(
                    {
                        "operation_id": row.key.rsplit(":", 1)[-1],
                        "provider": data.get("provider"),
                        "state": state,
                        "created_at": data.get("created_at"),
                        "recovery": recovery,
                    }
                )
        return {
            "operations": operations,
            "limits": {"max_seconds": self.settings.native_max_seconds, "max_concurrent": 1},
            "entitlements": {
                provider: self._entitlement_status(provider) for provider in ("retell", "vapi")
            },
        }

    def reconcile(self, tenant: str, owner: str, value: NativeCallInput) -> dict[str, Any]:
        """Retire only an exactly bound call with a verified terminal provider receipt."""
        owner_digest = hashlib.sha256(owner.encode()).hexdigest()
        key = NATIVE_OPERATION_PREFIX + value.provider + ":" + value.operation_id
        with self.service.sessions() as session:
            row = session.scalar(
                select(Operation).where(Operation.tenant_id == tenant, Operation.key == key)
            )
            if not owner or not row or row.result.get("owner") != owner_digest:
                raise DomainError("native_operation_not_found", 404)
            data = row.result
            call = session.get(Call, data.get("intent_id")) if data.get("intent_id") else None
            if (
                data.get("state") not in {"BOUND", "DONE"}
                or data.get("provider") != value.provider
                or not call
                or call.tenant_id != tenant
                or call.provider != value.provider
                or call.external_id != data.get("external_id")
                or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", call.external_id)
            ):
                raise DomainError("native_operation_requires_reconciliation", 409)
            external, agent, intent_id = call.external_id, call.agent_id, call.id
            already_done = data["state"] == "DONE" and call.state == "ended"
        if already_done:
            return self.status(tenant, owner)
        provider = self.settings.provider
        base_url = getattr(provider, value.provider + "_base_url").rstrip("/")
        secret = getattr(provider, value.provider + "_key").get_secret_value()
        try:
            receipt = self.reconciliation_transport.request(
                "GET",
                base_url + NATIVE_CALL_READ_PATHS[value.provider] + external,
                {"Authorization": "Bearer " + secret},
            )
        except Exception as exc:
            raise DomainError("native_reconciliation_unverified", 409) from exc
        id_field, agent_field, status_field = (
            ("call_id", "agent_id", "call_status")
            if value.provider == "retell"
            else ("id", "assistantId", "status")
        )
        metadata_source: object = receipt
        if value.provider == "vapi" and isinstance(receipt, dict):
            metadata_source = receipt.get("assistantOverrides")
        metadata = metadata_source.get("metadata") if isinstance(metadata_source, dict) else None
        if (
            not isinstance(receipt, dict)
            or receipt.get(id_field) != external
            or receipt.get(agent_field) != agent
            or not isinstance(metadata, dict)
            or metadata.get(NATIVE_OPERATION_METADATA_KEY) != value.operation_id
            or not isinstance(receipt.get(status_field), str)
            or receipt[status_field] not in NATIVE_TERMINAL_STATUSES[value.provider]
        ):
            raise DomainError("native_reconciliation_unverified", 409)
        with self.service.sessions.begin() as session:
            tenant_lock(session, tenant)
            row = session.scalar(
                select(Operation).where(Operation.tenant_id == tenant, Operation.key == key)
            )
            call = session.get(Call, intent_id)
            if (
                not row
                or row.result.get("owner") != owner_digest
                or row.result.get("state") not in {"BOUND", "DONE"}
                or row.result.get("intent_id") != intent_id
                or row.result.get("external_id") != external
                or not call
                or call.tenant_id != tenant
                or call.provider != value.provider
                or call.external_id != external
                or call.agent_id != agent
            ):
                raise DomainError("native_operation_requires_reconciliation", 409)
            if row.result["state"] != "DONE":
                call.state = "ended"
                row.result = {**row.result, "state": "DONE", "grant": None, "capability": None}
                audit(session, tenant, "native.call.reconciled", row.id)
        return self.status(tenant, owner)

    def _template(self) -> dict[str, Any]:
        path = self.settings.native_template_file
        if not path:
            raise DomainError("native_template_unavailable", 503)
        try:
            body = json.loads(path.read_text())["vapi-assistant"]
            model, server = body["model"], body["server"]
            tools = model["tools"]
            origin = self.settings.origins[0].rstrip("/")
            authorization = "Bearer " + self.settings.vapi_webhook_key.get_secret_value()
            valid = (
                body["voice"]["provider"] == "vapi"
                and body["voice"]["voiceId"] == self.service.profiles.vapi.voice_id
                and body["maxDurationSeconds"] == self.settings.native_max_seconds
                and body["artifactPlan"]
                == {
                    "recordingEnabled": False,
                    "loggingEnabled": False,
                    "pcapEnabled": False,
                    "transcriptPlan": {"enabled": True},
                }
                and isinstance(body["firstMessage"], str)
                and bool(body["firstMessage"].strip())
                and "recorded" not in body["firstMessage"].casefold()
                and VAPI_REQUIRED_SERVER_MESSAGES <= set(body["serverMessages"])
                and model["provider"] == self.settings.native_vapi_model_provider
                and model["model"] == self.settings.provider.vapi_model
                and server["url"] == origin + VAPI_EVENT_PATH
                and server["headers"]["Authorization"] == authorization
                and isinstance(tools, list)
                and 1 <= len(tools) <= len(BUSINESS_TOOLS)
                and {tool["function"]["name"] for tool in tools} <= BUSINESS_TOOLS
                and len({tool["function"]["name"] for tool in tools}) == len(tools)
                and all(
                    tool["server"]["url"] == origin + VAPI_TOOL_PATH
                    and tool["server"]["headers"]["Authorization"] == authorization
                    for tool in tools
                )
            )
        except (OSError, ValueError, KeyError, TypeError, IndexError):
            valid = False
        if not valid:
            raise DomainError("native_template_mismatch", 503)
        if not isinstance(body, dict):
            raise DomainError("native_template_mismatch", 503)
        return body

    def _preflight(self, provider: str) -> dict[str, Any] | None:
        profile = getattr(self.service.profiles, provider)
        if provider == "retell":
            if type(profile.version) is not int or profile.version < 0:
                raise DomainError("native_profile_version_unset", 503)
            path = self.settings.native_retell_approved_file
            if not path:
                raise DomainError("native_retell_approval_unavailable", 503)
            try:
                approved = json.loads(path.read_text())
                engine = approved["agent"]["response_engine"]
                llm_id, llm_version = engine["llm_id"], engine["version"]
            except (OSError, ValueError, KeyError, TypeError) as exc:
                raise DomainError("native_retell_approval_unavailable", 503) from exc
            if (
                not isinstance(llm_version, int)
                or not isinstance(llm_id, str)
                or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", llm_id)
                or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", profile.agent_id)
            ):
                raise DomainError("native_retell_approval_unavailable", 503)
            url = (
                self.settings.provider.retell_base_url.rstrip("/")
                + "/get-agent/"
                + profile.agent_id
                + "?version="
                + str(profile.version)
            )
            headers = {
                "Authorization": "Bearer " + self.settings.provider.retell_key.get_secret_value()
            }
            current = self.transport.request(
                "GET",
                url,
                headers,
            )
            llm = self.transport.request(
                "GET",
                self.settings.provider.retell_base_url.rstrip("/")
                + "/get-retell-llm/"
                + llm_id
                + "?version="
                + str(llm_version),
                headers,
            )
            if (
                current != approved["agent"]
                or llm != approved["llm"]
                or current.get("agent_id") != profile.agent_id
                or current.get("version") != profile.version
                or current.get("voice_id") != profile.voice_id
                or current.get("max_call_duration_ms") != self.settings.native_max_seconds * 1000
                or llm.get("model") != self.settings.provider.retell_model
            ):
                raise DomainError("native_profile_drift", 409)
            return None
        if not isinstance(profile.version, str) or not re.fullmatch(
            r"v[1-9][0-9]*", profile.version
        ):
            raise DomainError("native_profile_version_unset", 503)
        template = self._template()
        url = self.settings.provider.vapi_base_url.rstrip("/") + "/assistant/" + profile.agent_id
        current = self.transport.request(
            "GET",
            url,
            {"Authorization": "Bearer " + self.settings.provider.vapi_key.get_secret_value()},
        )
        if (
            current.get("id") != profile.agent_id
            or current.get("latestVersion") != profile.version
            or current.get("voice") != template["voice"]
            or current.get("maxDurationSeconds") != self.settings.native_max_seconds
            or current.get("model") != template["model"]
            or current.get("server") != template["server"]
            or current.get("transcriber") != template["transcriber"]
            or current.get("artifactPlan") != template["artifactPlan"]
            or current.get("serverMessages") != template["serverMessages"]
            or current.get("silenceTimeoutSeconds") != template["silenceTimeoutSeconds"]
        ):
            raise DomainError("native_profile_drift", 409)
        return template

    def _grant(self, provider: str, response: dict[str, Any]) -> dict[str, Any]:
        try:
            if provider == "retell":
                call_id = response["call_id"]
                grant = {
                    "provider": provider,
                    "callId": call_id,
                    "accessToken": response["access_token"],
                    "transport": response["transport"],
                    "iceServers": response["ice_servers"],
                    "expiresAt": int(response["expires_at"]),
                }
                valid = (
                    isinstance(grant["accessToken"], str)
                    and len(grant["accessToken"]) >= 16
                    and grant["transport"] == "gateway"
                    and isinstance(grant["iceServers"], list)
                    and len(grant["iceServers"]) <= 16
                    and grant["expiresAt"] > int(now().timestamp() * 1000)
                )
            else:
                call_id = response["id"]
                media = response["webCallUrl"]
                parsed = urlparse(media)
                suffix = self.settings.native_vapi_media_host_suffix
                token = response.get("transport", {}).get("callToken")
                grant = {
                    "provider": provider,
                    "callId": call_id,
                    "webCallUrl": media,
                    "expiresAt": int(
                        (now() + timedelta(seconds=self.settings.native_grant_seconds)).timestamp()
                        * 1000
                    ),
                }
                if token is not None:
                    grant["callToken"] = token
                valid = (
                    parsed.scheme == "https"
                    and bool(parsed.hostname)
                    and (parsed.hostname == suffix or parsed.hostname.endswith("." + suffix))
                    and not any((parsed.username, parsed.password, parsed.fragment, parsed.query))
                    and (token is None or isinstance(token, str))
                )
            valid = (
                valid
                and isinstance(call_id, str)
                and bool(re.fullmatch(r"[A-Za-z0-9_-]{1,100}", call_id))
            )
        except (KeyError, TypeError, ValueError, AttributeError):
            valid = False
        if not valid:
            raise DomainError("native_receipt_invalid", 502)
        return grant

    def _create_provider(
        self,
        provider: str,
        operation_id: str,
        capability: str,
        template: dict[str, Any] | None,
    ) -> dict[str, Any]:
        profile = getattr(self.service.profiles, provider)
        if provider == "retell":
            url = self.settings.provider.retell_base_url.rstrip("/") + NATIVE_CREATE_PATHS[provider]
            key = self.settings.provider.retell_key.get_secret_value()
            payload = {
                "agent_id": profile.agent_id,
                "agent_version": profile.version,
                "metadata": {
                    CALL_CAPABILITY_METADATA_KEY: capability,
                    NATIVE_OPERATION_METADATA_KEY: operation_id,
                },
                "agent_override": {
                    "agent": {"max_call_duration_ms": self.settings.native_max_seconds * 1000}
                },
            }
        else:
            if template is None:
                raise DomainError("native_template_unavailable", 503)
            url = self.settings.provider.vapi_base_url.rstrip("/") + NATIVE_CREATE_PATHS[provider]
            key = self.settings.provider.vapi_key.get_secret_value()
            server = deepcopy(template["server"])
            server["headers"][CALL_CAPABILITY_HEADER] = capability
            model = deepcopy(template["model"])
            for tool in model["tools"]:
                tool["server"]["headers"][CALL_CAPABILITY_HEADER] = capability
            payload = {
                "assistantId": profile.agent_id,
                "assistantVersion": profile.version,
                "roomDeleteOnUserLeaveEnabled": True,
                "assistantOverrides": {
                    "metadata": {NATIVE_OPERATION_METADATA_KEY: operation_id},
                    "maxDurationSeconds": self.settings.native_max_seconds,
                    "firstMessage": template["firstMessage"],
                    "voice": deepcopy(template["voice"]),
                    "transcriber": deepcopy(template["transcriber"]),
                    "artifactPlan": deepcopy(template["artifactPlan"]),
                    "serverMessages": deepcopy(template["serverMessages"]),
                    "silenceTimeoutSeconds": template["silenceTimeoutSeconds"],
                    "server": server,
                    "model": model,
                },
            }
        return self.transport.request(
            "POST",
            url,
            {"Authorization": "Bearer " + key},
            payload,
        )

    def _bound_grant(self, row: Operation) -> dict[str, Any]:
        data = row.result
        with self.service.sessions() as session:
            call = session.get(Call, data["intent_id"])
        return self._checked_bound_grant(row, call)

    def _checked_bound_grant(self, row: Operation, call: Call | None) -> dict[str, Any]:
        data = row.result
        if not call or call.tenant_id != row.tenant_id or call.external_id != data["external_id"]:
            raise DomainError("native_binding_unverified", 409)
        if call.state == "ended":
            raise DomainError("native_call_ended", 409)
        grant = self._open(data["grant"])
        if not isinstance(grant, dict):
            raise DomainError("native_recovery_unavailable", 503)
        if grant["expiresAt"] <= int(now().timestamp() * 1000):
            raise DomainError("native_grant_expired", 409)
        return grant

    def create(self, tenant: str, owner: str, value: NativeCallInput) -> dict[str, Any]:
        settings = self.settings
        if not settings.provider.voice_enabled or settings.stage != "pilot":
            raise DomainError("external_execution_disabled", 403)
        if not owner or not settings.provider_metadata_capability:
            raise DomainError("native_owner_required", 403)
        self._cipher()
        self._entitlement(value.provider)
        template = self._preflight(value.provider)
        owner_digest = hashlib.sha256(owner.encode()).hexdigest()
        key = NATIVE_OPERATION_PREFIX + value.provider + ":" + value.operation_id
        fingerprint = hashlib.sha256((owner_digest + ":" + value.provider).encode()).hexdigest()
        existing_state: str | None = None
        existing_row: Operation | None = None
        with self.service.sessions.begin() as session:
            tenant_lock(session, NATIVE_ACCOUNT_LOCK)
            existing = session.scalar(
                select(Operation).where(Operation.tenant_id == tenant, Operation.key == key)
            )
            if existing:
                if (
                    existing.fingerprint != fingerprint
                    or existing.result.get("owner") != owner_digest
                ):
                    raise DomainError("native_operation_conflict", 409)
                existing_state, existing_row = existing.result["state"], existing
            else:
                active = session.scalars(
                    select(Operation).where(
                        Operation.key.like(NATIVE_OPERATION_PREFIX + "%"),
                    )
                ).all()
                for operation in active:
                    if operation.result["state"] == "BOUND":
                        call = session.get(Call, operation.result["intent_id"])
                        if call and call.state == "ended":
                            operation.result = {**operation.result, "state": "DONE", "grant": None}
                            continue
                    if operation.result["state"] != "DONE":
                        raise DomainError("native_call_capacity_reached", 429)
                reserved = Operation(
                    id=identity(),
                    tenant_id=tenant,
                    key=key,
                    fingerprint=fingerprint,
                    result={
                        "state": "RESERVED",
                        "owner": owner_digest,
                        "provider": value.provider,
                        "created_at": now().isoformat(),
                    },
                )
                session.add(reserved)
                audit(session, tenant, "native.operation.reserved", reserved.id)
        if existing_row:
            if existing_state == "BOUND":
                return self._bound_grant(existing_row)
            if existing_state == "EXTERNAL_CREATED":
                return self._bind(tenant, existing_row)
            raise DomainError("native_operation_requires_reconciliation", 409)
        prepared = self.providers.prepare_intent(tenant, value.provider)
        with self.service.sessions.begin() as session:
            tenant_lock(session, tenant)
            row = session.scalar(
                select(Operation).where(Operation.tenant_id == tenant, Operation.key == key)
            )
            if not row or row.result["state"] != "RESERVED":
                raise DomainError("native_operation_requires_reconciliation", 409)
            row.result = {
                **row.result,
                "state": "REQUEST_PENDING",
                "intent_id": prepared["intent_id"],
                "capability": self._seal(prepared["capability"]),
            }
            audit(session, tenant, "native.create.pending", row.id)
        try:
            response = self._create_provider(
                value.provider, value.operation_id, prepared["capability"], template
            )
            grant = self._grant(value.provider, response)
        except Exception as exc:
            with self.service.sessions.begin() as session:
                tenant_lock(session, tenant)
                row = session.scalar(
                    select(Operation).where(Operation.tenant_id == tenant, Operation.key == key)
                )
                if row and row.result["state"] == "REQUEST_PENDING":
                    row.result = {**row.result, "state": "UNKNOWN"}
                    audit(session, tenant, "native.create.unknown", row.id)
            raise DomainError("native_create_unverified", 409) from exc
        with self.service.sessions.begin() as session:
            tenant_lock(session, tenant)
            row = session.scalar(
                select(Operation).where(Operation.tenant_id == tenant, Operation.key == key)
            )
            if not row or row.result["state"] != "REQUEST_PENDING":
                raise DomainError("native_operation_requires_reconciliation", 409)
            row.result = {
                **row.result,
                "state": "EXTERNAL_CREATED",
                "external_id": grant["callId"],
                "grant": self._seal(grant),
            }
            audit(session, tenant, "native.create.received", row.id)
        return self._bind(tenant, row)

    def _bind(self, tenant: str, row: Operation) -> dict[str, Any]:
        data = row.result
        self.providers.bind_intent(
            tenant, CallIntentBinding(intent_id=data["intent_id"], external_id=data["external_id"])
        )
        with self.service.sessions.begin() as session:
            tenant_lock(session, tenant)
            current = session.scalar(
                select(Operation).where(Operation.id == row.id, Operation.tenant_id == tenant)
            )
            if not current or current.result["state"] not in {"EXTERNAL_CREATED", "BOUND"}:
                raise DomainError("native_operation_requires_reconciliation", 409)
            current.result = {**current.result, "state": "BOUND", "capability": None}
            audit(session, tenant, "native.call.bound", current.id)
        return self._bound_grant(current)
