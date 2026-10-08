"""Relational state, constraints and database-owned queue leases."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from .settings import Settings


def now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (UniqueConstraint("tenant_id", "email"),)
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(254))
    phone: Mapped[str] = mapped_column(String(25))
    notes: Mapped[str] = mapped_column(Text, default="")


class Appointment(Base):
    __tablename__ = "appointments"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    contact_id: Mapped[str] = mapped_column(ForeignKey("contacts.id"))
    call_id: Mapped[str | None] = mapped_column(String(100))
    service: Mapped[str] = mapped_column(String(100))
    start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(40), index=True)
    external_id: Mapped[str | None] = mapped_column(String(200))
    revision: Mapped[int] = mapped_column(Integer, default=1)
    desired: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class Operation(Base):
    __tablename__ = "operations"
    __table_args__ = (UniqueConstraint("tenant_id", "key"),)
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    key: Mapped[str] = mapped_column(String(100))
    fingerprint: Mapped[str] = mapped_column(String(64))
    result: Mapped[dict[str, Any]] = mapped_column(JSON)


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "kind", "operation_key"),
        Index("jobs_ready", "status", "next_run"),
    )
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    kind: Mapped[str] = mapped_column(String(40))
    operation_key: Mapped[str] = mapped_column(String(150))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(40), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_run: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lease_token: Mapped[str | None] = mapped_column(String(100))
    receipt: Mapped[str | None] = mapped_column(String(200))
    detail: Mapped[str] = mapped_column(String(200), default="queued")


class Call(Base):
    __tablename__ = "calls"
    __table_args__ = (UniqueConstraint("provider", "external_id"),)
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    provider: Mapped[str] = mapped_column(String(20))
    external_id: Mapped[str] = mapped_column(String(100))
    agent_id: Mapped[str] = mapped_column(String(100))
    capability_digest: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(40), default="registered")
    transcript: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Inbox(Base):
    __tablename__ = "inbox"
    __table_args__ = (UniqueConstraint("provider", "event_key"),)
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    provider: Mapped[str] = mapped_column(String(20))
    event_key: Mapped[str] = mapped_column(String(200))
    call_id: Mapped[str] = mapped_column(ForeignKey("calls.id"))
    event: Mapped[str] = mapped_column(String(100))


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    text: Mapped[str] = mapped_column(Text)
    checksum: Mapped[str] = mapped_column(String(64))
    revision: Mapped[int] = mapped_column(Integer, default=1)
    fact_key: Mapped[str | None] = mapped_column(String(100))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Record(Base):
    __tablename__ = "records"
    __table_args__ = (UniqueConstraint("tenant_id", "kind", "key"),)
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    kind: Mapped[str] = mapped_column(String(40))
    key: Mapped[str] = mapped_column(String(100))
    value: Mapped[dict[str, Any]] = mapped_column(JSON)
    revision: Mapped[int] = mapped_column(Integer, default=1)


class Audit(Base):
    __tablename__ = "audit"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    action: Mapped[str] = mapped_column(String(100))
    target: Mapped[str] = mapped_column(String(100))
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    kind: Mapped[str] = mapped_column(String(16), index=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    payload: Mapped[str] = mapped_column(Text)
    expires: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ExternalRecord(Base):
    """Durable local simulator ledger, separate commit from application outcome."""

    __tablename__ = "local_connector_records"
    id: Mapped[str] = mapped_column(String(200), primary_key=True)
    kind: Mapped[str] = mapped_column(String(40))
    value: Mapped[dict[str, Any]] = mapped_column(JSON)


def make_sessions(settings: Settings) -> sessionmaker[Session]:
    engine = create_engine(
        settings.database_url.get_secret_value(),
        pool_size=settings.pool_size,
        max_overflow=0,
        pool_timeout=settings.pool_timeout_seconds,
        pool_pre_ping=True,
        hide_parameters=True,
    )
    return sessionmaker(engine, expire_on_commit=False)


def tenant_lock(session: Session, tenant: str) -> None:
    # Stable database advisory lock serializes slot decisions across API replicas.
    session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:tenant, 0))"), {"tenant": tenant}
    )
