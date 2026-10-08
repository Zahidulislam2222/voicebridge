"""Loopback core API. Capabilities are server-checked independently of UI roles."""

import asyncio
import hmac
import json
from collections.abc import Awaitable, Callable
from datetime import datetime
from importlib.metadata import version
from typing import Any, Literal

from fastapi import Depends, FastAPI, Header, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy import select, text
from starlette.concurrency import run_in_threadpool
from starlette.middleware.cors import CORSMiddleware

from .auth import Authentication
from .connectors import Delivery, GoogleCalendar, LocalCalendar
from .contracts import (
    AgentInput,
    AgentView,
    AppointmentView,
    BookingInput,
    CallIntentBinding,
    CallIntentInput,
    ChangeInput,
    DocumentInput,
    DomainError,
    EvaluationFixtureView,
    StateView,
    ToolInput,
)
from .db import Record, make_sessions, now, tenant_lock
from .documents import parse_pdf
from .protocol import (
    BUSINESS_READ_TOOLS,
    BUSINESS_TOOLS,
    CALL_CAPABILITY_HEADER,
    CORE_DISTRIBUTION,
    LOCAL_CALENDAR_KIND,
    MANAGEMENT_READ_TOOLS,
    MANAGEMENT_TOOLS,
    MCP_COMPATIBLE_VERSIONS,
    MCP_VERSION,
    RETELL_SIGNATURE_HEADER,
)
from .providers import Providers, retell_verify
from .service import Service, identity
from .settings import Settings
from .worker import Worker


def create_app(settings: Settings) -> FastAPI:
    sessions = make_sessions(settings)
    calendar = (
        GoogleCalendar(settings)
        if settings.provider.enabled
        else LocalCalendar(sessions, LOCAL_CALENDAR_KIND)
    )
    service = Service(settings, sessions, calendar)
    worker = Worker(service, Delivery(settings, sessions))
    providers = Providers(service, worker)
    app = FastAPI(
        title=service.profiles.application_name,
        version=version(CORE_DISTRIBUTION),
        docs_url=None,
        redoc_url=None,
    )
    app.state.service, app.state.worker, app.state.providers = service, worker, providers
    authentication = Authentication(settings, sessions)
    app.state.authentication = authentication
    authentication.install(app)
    pdf_slots = asyncio.BoundedSemaphore(settings.pdf_max_concurrent_parsers)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "MCP-Protocol-Version", "X-CSRF-Token"],
        allow_credentials=bool(settings.auth),
    )

    @app.middleware("http")
    async def boundaries(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        origin = request.headers.get("origin")
        if origin and origin not in settings.origins:
            return JSONResponse({"error": "untrusted_origin"}, status_code=403)
        size = 0
        chunks = []
        async for chunk in request.stream():
            size += len(chunk)
            if size > settings.max_body_bytes:
                return JSONResponse({"error": "request_too_large"}, status_code=413)
            chunks.append(chunk)
        request._body = b"".join(chunks)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.exception_handler(DomainError)
    async def domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse({"error": exc.code}, status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def request_error(_: Request, __: RequestValidationError) -> JSONResponse:
        return JSONResponse({"error": "invalid_request"}, status_code=422)

    @app.exception_handler(ValidationError)
    async def validation_error(_: Request, __: ValidationError) -> JSONResponse:
        return JSONResponse({"error": "invalid_input"}, status_code=422)

    def check(credential: str, expected: str) -> None:
        if not expected or not hmac.compare_digest(credential, "Bearer " + expected):
            raise DomainError("authorization_required", 401)

    def authorize(request: Request, authorization: str = Header(default="")) -> str:
        if settings.auth and (settings.stage == "pilot" or not authorization):
            tenant = authentication.authorize(request)
        else:
            if settings.stage == "pilot":
                raise DomainError("authorization_required", 401)
            check(authorization, settings.operator_key.get_secret_value())
            tenant = settings.tenant_id
        # Persisted per-tenant fixed-window limit, shared across replicas.
        with sessions.begin() as s:
            tenant_lock(s, tenant)
            minute = int(now().timestamp() // 60)
            row = s.scalar(
                select(Record).where(
                    Record.tenant_id == tenant, Record.kind == "limit", Record.key == "operator"
                )
            )
            count = int(row.value["count"]) if row and row.value["minute"] == minute else 0
            if count >= settings.max_operations_per_minute:
                raise DomainError("rate_limit", 429)
            if not row:
                s.add(
                    Record(
                        id=identity(),
                        tenant_id=tenant,
                        kind="limit",
                        key="operator",
                        value={"minute": minute, "count": 1},
                    )
                )
            else:
                row.value = {"minute": minute, "count": count + 1}
        return tenant

    @app.get("/health/live")
    def liveness() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/health/ready")
    def readiness() -> JSONResponse:
        try:
            with sessions() as s:
                s.execute(text("SELECT 1"))
                s.execute(select(Record.id).limit(1))
            return JSONResponse({"status": "ready", "stage": settings.stage})
        except Exception:
            return JSONResponse({"status": "unavailable"}, status_code=503)

    @app.get("/api/bootstrap")
    def bootstrap(tenant: str = Depends(authorize)) -> dict[str, Any]:
        return {
            "business": service.business.name,
            "timezone": service.business.timezone,
            "services": service.business.services,
            "synthetic": not settings.provider.enabled,
            "profiles": service.profiles.model_dump(),
            "stage": "local-core",
        }

    @app.get("/api/state", response_model=StateView)
    def state(tenant: str = Depends(authorize)) -> dict[str, Any]:
        return service.snapshot(tenant)

    @app.get("/api/availability")
    def availability(
        start: datetime, service_name: str, tenant: str = Depends(authorize)
    ) -> dict[str, Any]:
        return service.availability(tenant, start, service_name)

    @app.post("/api/bookings", response_model=AppointmentView)
    def book(value: BookingInput, tenant: str = Depends(authorize)) -> dict[str, Any]:
        result = service.book(tenant, value)
        providers.drain_calendar(tenant, result["booking_id"])
        return service.appointment(tenant, result["booking_id"])

    @app.get("/api/bookings/{booking_id}", response_model=AppointmentView)
    def get_booking(booking_id: str, tenant: str = Depends(authorize)) -> dict[str, Any]:
        return service.appointment(tenant, booking_id)

    @app.post("/api/bookings/{booking_id}", response_model=AppointmentView)
    def change(
        booking_id: str, value: ChangeInput, tenant: str = Depends(authorize)
    ) -> dict[str, Any]:
        result = service.change(tenant, booking_id, value)
        providers.drain_calendar(tenant, result["booking_id"])
        return service.appointment(tenant, booking_id)

    @app.post("/api/jobs/{job_id}/replay", status_code=204)
    def replay(job_id: str, tenant: str = Depends(authorize)) -> None:
        service.replay(tenant, job_id)

    @app.post("/api/jobs/{job_id}/reconcile", status_code=204)
    def reconcile(job_id: str, tenant: str = Depends(authorize)) -> None:
        worker.reconcile(tenant, job_id)
        worker.run_one(job_id)

    @app.post("/api/knowledge")
    def document(value: DocumentInput, tenant: str = Depends(authorize)) -> dict[str, str]:
        return {"id": service.document(tenant, value)}

    @app.put("/api/knowledge/{doc_id}")
    def change_document(
        doc_id: str, value: DocumentInput, tenant: str = Depends(authorize)
    ) -> dict[str, str]:
        return {"id": service.document(tenant, value, doc_id)}

    @app.delete("/api/knowledge/{doc_id}", status_code=204)
    def delete_document(doc_id: str, tenant: str = Depends(authorize)) -> None:
        service.delete_document(tenant, doc_id)

    @app.post("/api/knowledge/import")
    async def import_document(
        request: Request, name: str, tenant: str = Depends(authorize)
    ) -> dict[str, str]:
        body = await request.body()
        if len(body) > settings.max_document_bytes:
            raise DomainError("document_too_large", 413)
        mime = request.headers.get("content-type", "").split(";")[0]
        try:
            if mime in {"text/plain", "text/markdown"} and name.lower().endswith((".txt", ".md")):
                value = body.decode("utf-8")
            elif mime == "application/pdf" and name.lower().endswith(".pdf"):
                if pdf_slots.locked():
                    raise DomainError("pdf_capacity_busy", 429)
                async with pdf_slots:
                    value = await run_in_threadpool(parse_pdf, body, settings)
            else:
                raise DomainError("unsupported_document_type", 415)
        except (ValueError, UnicodeError) as exc:
            raise DomainError("document_parse_failed", 422) from exc
        return {"id": service.document(tenant, DocumentInput(name=name, text=value))}

    @app.get("/api/knowledge/answer")
    def answer(query: str, tenant: str = Depends(authorize)) -> dict[str, Any]:
        return service.answer(tenant, query)

    @app.put("/api/agent", response_model=AgentView)
    def agent(value: AgentInput, tenant: str = Depends(authorize)) -> dict[str, Any]:
        return service.save_agent(tenant, value)

    @app.post("/api/evaluations")
    def evaluate(tenant: str = Depends(authorize)) -> dict[str, Any]:
        return providers.evaluate(tenant)

    @app.post("/api/evaluations/{fixture_id}/cleanup", response_model=EvaluationFixtureView)
    def cleanup_evaluation(fixture_id: str, tenant: str = Depends(authorize)) -> dict[str, Any]:
        return providers.cleanup_fixture(tenant, fixture_id)

    @app.post("/api/tools")
    def tool(value: ToolInput, tenant: str = Depends(authorize)) -> dict[str, Any]:
        return providers.invoke(tenant, value.name, value.arguments)

    @app.post("/api/calls/prepare")
    def prepare_call_intent(
        value: CallIntentInput, tenant: str = Depends(authorize)
    ) -> dict[str, Any]:
        return providers.prepare_intent(tenant, value.provider)

    @app.post("/api/calls/bind")
    def bind_call_intent(
        value: CallIntentBinding, tenant: str = Depends(authorize)
    ) -> dict[str, str]:
        return providers.bind_intent(tenant, value)

    @app.post("/api/calls/register")
    def register(
        provider: Literal["retell", "vapi"],
        external_id: str,
        agent_id: str,
        tenant: str = Depends(authorize),
    ) -> dict[str, str]:
        return providers.register(tenant, provider, external_id, agent_id)

    @app.post("/providers/{provider}/{surface}")
    async def provider_request(
        provider: Literal["retell", "vapi"], surface: Literal["events", "tools"], request: Request
    ) -> dict[str, Any]:
        body = await request.body()
        if provider == "retell":
            if not retell_verify(
                body,
                request.headers.get(RETELL_SIGNATURE_HEADER, ""),
                settings.retell_webhook_key.get_secret_value(),
                settings.webhook_tolerance_seconds,
            ):
                raise DomainError("invalid_retell_signature", 401)
        else:
            check(
                request.headers.get("authorization", ""),
                settings.vapi_webhook_key.get_secret_value(),
            )
        try:
            value = json.loads(body)
            capability = providers.envelope_capability(
                provider, value, request.headers.get(CALL_CAPABILITY_HEADER)
            )
            return (
                providers.event(provider, value, capability)
                if surface == "events"
                else providers.tools(provider, value, capability)
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise DomainError("invalid_provider_envelope", 422) from exc

    @app.post("/mcp/{surface}")
    async def mcp(surface: Literal["business", "management"], request: Request) -> Response:
        expected = settings.business_key if surface == "business" else settings.management_key
        read_key = (
            settings.business_read_key if surface == "business" else settings.management_read_key
        )
        credential = request.headers.get("authorization", "")
        read_only = hmac.compare_digest(credential, "Bearer " + read_key.get_secret_value())
        if not read_only:
            check(credential, expected.get_secret_value())
        version = request.headers.get("mcp-protocol-version")
        if version and version not in MCP_COMPATIBLE_VERSIONS:
            return JSONResponse({"error": "unsupported_mcp_version"}, status_code=400)
        rpc_id: str | int | None = None

        def rpc_error(code: int, message: str) -> JSONResponse:
            return JSONResponse(
                {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": code, "message": message}}
            )

        try:
            rpc = await request.json()
        except ValueError:
            return rpc_error(-32700, "Parse error")
        if not isinstance(rpc, dict) or rpc.get("jsonrpc") != "2.0":
            return rpc_error(-32600, "Invalid request")
        method, rpc_id = rpc.get("method"), rpc.get("id")
        if (
            not isinstance(method, str)
            or isinstance(rpc_id, bool)
            or (rpc_id is not None and not isinstance(rpc_id, (str, int)))
        ):
            rpc_id = None
            return rpc_error(-32600, "Invalid request")
        if "id" not in rpc:
            if method.startswith("notifications/"):
                return Response(status_code=202)
            return rpc_error(-32600, "Request id required")
        try:
            allowed = BUSINESS_TOOLS if surface == "business" else MANAGEMENT_TOOLS
            if read_only:
                allowed = BUSINESS_READ_TOOLS if surface == "business" else MANAGEMENT_READ_TOOLS
            params = rpc.get("params", {})
            if not isinstance(params, dict):
                return rpc_error(-32602, "Invalid parameters")
            result: dict[str, Any]
            if method == "initialize":
                requested = params.get("protocolVersion")
                if not isinstance(requested, str):
                    return rpc_error(-32602, "Protocol version required")
                result = {
                    "protocolVersion": (
                        requested if requested in MCP_COMPATIBLE_VERSIONS else MCP_VERSION
                    ),
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": app.title, "version": app.version},
                }
            elif method == "tools/list":
                definitions = service.profiles.model_dump()["tools"]
                result = {"tools": [definitions[name] for name in sorted(allowed)]}
            elif method == "tools/call":
                name = params["name"]
                if not isinstance(name, str) or name not in allowed:
                    return rpc_error(-32602, "Unknown or unavailable tool")
                try:
                    output = providers.invoke(
                        settings.tenant_id,
                        name,
                        params.get("arguments", {}),
                        management=surface == "management",
                    )
                    result = {
                        "content": [{"type": "text", "text": json.dumps(output)}],
                        "isError": False,
                    }
                except (DomainError, ValidationError, ValueError, TypeError) as exc:
                    error = exc.code if isinstance(exc, DomainError) else "invalid_tool_arguments"
                    result = {"content": [{"type": "text", "text": error}], "isError": True}
            elif method == "ping":
                result = {}
            else:
                return rpc_error(-32601, "Method not found")
            return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "result": result})
        except (KeyError, TypeError, ValueError):
            return rpc_error(-32602, "Invalid parameters")

    return app
