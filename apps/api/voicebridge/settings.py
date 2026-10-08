"""One typed environment boundary; no secret is returned by public bootstrap."""

from pathlib import Path
from string import Formatter
from typing import Any, Literal
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .contracts import DocumentInput


class AuthSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    discovery_url: str
    issuer: str
    client_id: str
    client_secret: SecretStr
    redirect_uri: str
    post_login_uri: str
    scope: str
    algorithms: list[str]
    encryption_key: SecretStr
    access_file: Path
    cookie_name: str
    login_cookie_name: str
    cookie_secure: bool
    session_seconds: int = Field(gt=0)
    idle_seconds: int = Field(gt=0)
    login_seconds: int = Field(gt=0)
    timeout_seconds: float = Field(gt=0)
    max_pending_logins: int = Field(gt=0)
    max_sessions: int = Field(gt=0)

    @model_validator(mode="after")
    def valid_auth(self) -> "AuthSettings":
        from cryptography.fernet import Fernet

        Fernet(self.encryption_key.get_secret_value().encode())
        for value in (self.discovery_url, self.issuer, self.redirect_uri, self.post_login_uri):
            parsed = urlparse(value)
            if parsed.username or parsed.password or parsed.query:
                raise ValueError("Authentication endpoints cannot contain credentials or queries")
            if parsed.scheme != "https" and not (
                not self.cookie_secure
                and parsed.scheme == "http"
                and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
            ):
                raise ValueError("Authentication endpoints require HTTPS or isolated loopback")
        if "openid" not in self.scope.split() or not self.algorithms or "none" in self.algorithms:
            raise ValueError("OIDC requires openid scope and signed tokens")
        if self.cookie_name == self.login_cookie_name:
            raise ValueError("Login and authenticated cookie names must differ")
        if self.cookie_secure and not all(
            name.startswith("__Host-") for name in (self.cookie_name, self.login_cookie_name)
        ):
            raise ValueError("Secure pilot cookies require host-only names")
        return self


class AccessBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    issuer: str
    subject: str | None = None
    verified_email: str | None = None
    tenant_id: str
    role: Literal["owner", "operator", "viewer"]

    @model_validator(mode="after")
    def identity_binding(self) -> "AccessBinding":
        if bool(self.subject) == bool(self.verified_email):
            raise ValueError("Bind exactly one immutable subject or verified bootstrap email")
        return self


class AccessPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bindings: list[AccessBinding]


class ProviderSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, str_strip_whitespace=True)
    base_url: str
    calendar_path: str
    contacts_path: str
    token_url: str
    retell_base_url: str
    vapi_base_url: str
    elevenlabs_base_url: str
    retell_model: str
    vapi_model: str
    elevenlabs_model: str
    timeout_seconds: float = Field(gt=0)
    user_agent: str = Field(min_length=1, pattern=r"^[^\r\n]+$")
    enabled: bool
    vapi_owner_resolved: bool
    calendar_id: str
    google_client_id: str
    google_client_secret: SecretStr = Field(min_length=1)
    google_refresh_token: SecretStr = Field(min_length=1)
    hubspot_key: SecretStr = Field(min_length=1)
    retell_key: SecretStr = Field(min_length=1)
    vapi_key: SecretStr = Field(min_length=1)
    elevenlabs_key: SecretStr = Field(min_length=1)

    @model_validator(mode="after")
    def secure_endpoints(self) -> "ProviderSettings":
        for endpoint in (
            self.base_url,
            self.contacts_path,
            self.token_url,
            self.retell_base_url,
            self.vapi_base_url,
            self.elevenlabs_base_url,
        ):
            parsed = urlparse(endpoint)
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError(
                    "Provider endpoints require HTTPS without embedded credentials or parameters"
                )
        return self


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="VB_",
        env_nested_delimiter="__",
        extra="ignore",
        hide_input_in_errors=True,
    )
    database_url: SecretStr
    stage: Literal["local", "pilot"] = "local"
    auth: AuthSettings | None = None
    observation_file: Path = Path("config/observation-profiles.json")
    migration_config: Path
    operator_key: SecretStr = Field(min_length=24)
    business_key: SecretStr = Field(min_length=24)
    management_key: SecretStr = Field(min_length=24)
    business_read_key: SecretStr = Field(min_length=24)
    management_read_key: SecretStr = Field(min_length=24)
    retell_webhook_key: SecretStr = Field(min_length=1)
    vapi_webhook_key: SecretStr = Field(min_length=1)
    provider_metadata_capability: bool = False
    call_intent_seconds: int = Field(default=300, gt=0)
    max_pending_call_intents: int = Field(default=100, gt=0)
    tenant_id: str
    host: str
    port: int = Field(gt=0, lt=65536)
    origins: list[str]
    data_file: Path
    evaluation_file: Path
    template_file: Path
    profile_file: Path
    max_body_bytes: int = Field(gt=0)
    max_document_bytes: int = Field(gt=0)
    pdf_max_pages: int = Field(gt=0)
    pdf_memory_bytes: int = Field(gt=0)
    pdf_timeout_seconds: float = Field(gt=0)
    pdf_max_concurrent_parsers: int = Field(gt=0)
    max_documents: int = Field(gt=0)
    max_records_per_page: int = Field(gt=0, le=1000)
    max_query_chars: int = Field(gt=0)
    search_language: str
    search_limit: int = Field(gt=0)
    knowledge_max_age_days: int = Field(gt=0)
    lease_seconds: int = Field(gt=0)
    worker_poll_seconds: float = Field(gt=0)
    max_attempts: int = Field(gt=0)
    backoff_seconds: float = Field(gt=0)
    pool_size: int = Field(gt=0)
    pool_timeout_seconds: float = Field(gt=0)
    max_operations_per_minute: int = Field(gt=0)
    webhook_tolerance_seconds: int = Field(gt=0)
    smtp_host: str
    smtp_port: int = Field(gt=0, lt=65536)
    smtp_timeout_seconds: float = Field(gt=0)
    smtp_from: str
    n8n_url: str
    n8n_key: SecretStr = Field(min_length=1)
    followup_transport: Literal["capture", "n8n"]
    provider: ProviderSettings

    @model_validator(mode="after")
    def safe_local(self) -> "Settings":
        if self.stage == "pilot":
            if not self.auth or not self.auth.cookie_secure:
                raise ValueError("Public pilot requires configured secure OIDC sessions")
            if self.provider.enabled:
                raise ValueError("Pilot publication initially keeps real providers disabled")
            if any(urlparse(origin).scheme != "https" for origin in self.origins):
                raise ValueError("Pilot origins require HTTPS")
        elif self.host not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("Core preview must bind to loopback until the public release gate")
        if not self.database_url.get_secret_value().startswith("postgresql+psycopg://"):
            raise ValueError("Core requires PostgreSQL")
        for origin in self.origins:
            if self.stage == "local" and urlparse(origin).hostname not in {
                "127.0.0.1",
                "localhost",
                "::1",
            }:
                raise ValueError("Only loopback origins allowed for this stage")
        if self.stage == "local" and self.smtp_host not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("Only local SMTP capture allowed")
        if self.stage == "local" and urlparse(self.n8n_url).hostname not in {
            "127.0.0.1",
            "localhost",
            "::1",
        }:
            raise ValueError("Only local n8n allowed")
        if self.stage == "pilot" and self.followup_transport != "capture":
            raise ValueError("Initial public pilot only permits capture delivery")
        if (
            len(
                {
                    self.operator_key.get_secret_value(),
                    self.business_key.get_secret_value(),
                    self.management_key.get_secret_value(),
                    self.business_read_key.get_secret_value(),
                    self.management_read_key.get_secret_value(),
                }
            )
            != 5
        ):
            raise ValueError("Capability credentials must differ")
        return self


def load_settings(env_file: str | Path) -> Settings:
    return Settings(_env_file=env_file)  # type: ignore[call-arg]


class ObservationProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(gt=0)
    url: str
    interval_seconds: float = Field(ge=1)
    timeout_seconds: float = Field(gt=0)
    gap_factor: float = Field(gt=1)
    max_recent_samples: int = Field(gt=0)
    state_file: Path
    expected_status: int = Field(ge=100, le=599)
    observation_days: int = Field(gt=0)
    target_percent: float = Field(gt=0, le=100)

    @model_validator(mode="after")
    def endpoint(self) -> "ObservationProfile":
        parsed = urlparse(self.url)
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Observation cannot include credential material")
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Observation requires a configured HTTP endpoint")
        return self


class Business(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    name: str
    timezone: str
    services: dict[str, int]
    opening_hour: int = Field(ge=0, le=23)
    closing_hour: int = Field(ge=1, le=24)
    weekdays: list[int]
    slot_minutes: int = Field(gt=0)
    advance_days: int = Field(gt=0)
    greeting: str
    handoff: str
    voice_id: str
    messages: dict[str, str]
    knowledge: list[dict[str, str]]

    @model_validator(mode="after")
    def hours(self) -> "Business":
        ZoneInfo(self.timezone)
        if self.opening_hour >= self.closing_hour or not self.services:
            raise ValueError("Invalid business hours/services")
        if any(v <= 0 for v in self.services.values()):
            raise ValueError("Service duration must be positive")
        if not self.weekdays or any(day < 0 or day > 6 for day in self.weekdays):
            raise ValueError("Invalid business weekdays")
        message_keys = {"confirmed", "pending", "missing", "conflict"}
        if set(self.messages) != message_keys:
            raise ValueError("Missing or unknown business messages")
        if any(not value.strip() for value in self.messages.values()):
            raise ValueError("Business messages must be nonempty")
        if any(set(item) != {"name", "text"} or not all(item.values()) for item in self.knowledge):
            raise ValueError("Knowledge needs nonempty name and text")
        return self


class FollowupTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)
    from_name: str = Field(min_length=1)

    @model_validator(mode="after")
    def safe_fields(self) -> "FollowupTemplate":
        allowed = {"name", "service", "start", "timezone", "booking_id"}
        for _, field, spec, conversion in Formatter().parse(self.body):
            if field is not None and (field not in allowed or spec or conversion):
                raise ValueError("Unknown or unsafe follow-up template field")
        if any(c in self.subject + self.from_name for c in "\r\n"):
            raise ValueError("Invalid mail header")
        return self


class MaintainedData(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class EvaluationCase(MaintainedData):
    id: str = Field(min_length=1)
    kind: Literal[
        "knowledge",
        "confirmation",
        "invalid_slot",
        "isolation",
        "provider_parity",
        "booking",
        "adversarial_retrieval",
    ]
    expected: str = Field(min_length=1)
    query: str = Field(min_length=1)


class EvaluationSuite(MaintainedData):
    revision: int = Field(ge=1)
    contact: dict[str, str]
    agent_id: str = Field(min_length=1)
    adversarial_document: DocumentInput
    cases: list[EvaluationCase]

    @model_validator(mode="after")
    def complete(self) -> "EvaluationSuite":
        if set(self.contact) != {"name", "email", "phone"}:
            raise ValueError("Evaluation contact is incomplete")
        if not self.contact["email"].endswith(".invalid"):
            raise ValueError("Evaluation contact must be synthetic")
        if len({case.id for case in self.cases}) != len(self.cases):
            raise ValueError("Evaluation case ids must be unique")
        return self


class ProviderProfile(MaintainedData):
    agent_id: str
    voice_id: str
    state: str = Field(min_length=1)


class ToolDefinition(MaintainedData):
    name: str
    description: str = Field(min_length=1)
    inputSchema: dict[str, Any]


class ProviderProfiles(MaintainedData):
    application_name: str = Field(min_length=1)
    revision: int = Field(ge=1)
    retell: ProviderProfile
    vapi: ProviderProfile
    instruction: str = Field(min_length=1)
    tools: dict[str, ToolDefinition]

    @model_validator(mode="after")
    def tool_contracts(self) -> "ProviderProfiles":
        from .protocol import BUSINESS_TOOLS, MANAGEMENT_TOOLS

        if set(self.tools) != BUSINESS_TOOLS | MANAGEMENT_TOOLS:
            raise ValueError("Tool definitions do not match supported tools")
        for name, tool in self.tools.items():
            if name != tool.name or tool.inputSchema.get("type") != "object":
                raise ValueError("Invalid tool definition")
        return self


def read_data(path: Path) -> dict[str, Any]:
    import json

    value: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Expected validated object data")
    return value
