"""Durable worker. Leases fence DB writes; uncertain external sends are visible."""

from datetime import timedelta
from typing import Any

from sqlalchemy import select

from .connectors import Delivery, RetryableFailure, UnknownOutcome
from .contracts import DomainError
from .db import Appointment, Contact, Job, now, tenant_lock
from .service import Service, audit, identity


class Worker:
    def __init__(self, service: Service, delivery: Delivery) -> None:
        self.service, self.delivery = service, delivery

    def claim(self, job_id: str | None = None) -> tuple[str, str] | None:
        with self.service.sessions.begin() as s:
            expired = list(
                s.scalars(
                    select(Job)
                    .where(
                        Job.tenant_id == self.service.settings.tenant_id,
                        Job.status == "running",
                        Job.lease_until < now(),
                    )
                    .with_for_update(skip_locked=True)
                    .limit(self.service.settings.max_records_per_page)
                )
            )
            for expired_row in expired:
                expired_row.status = "pending" if expired_row.kind == "calendar" else "unknown"
                expired_row.detail = "expired_lease_requires_reconciliation"
                expired_row.lease_token, expired_row.lease_until = None, None
            query = select(Job).where(
                Job.tenant_id == self.service.settings.tenant_id,
                Job.status.in_(["pending", "failed"]),
                Job.next_run <= now(),
            )
            if job_id:
                query = query.where(Job.id == job_id)
            row = s.scalar(query.order_by(Job.next_run).with_for_update(skip_locked=True).limit(1))
            if not row:
                return None
            if row.attempts >= self.service.settings.max_attempts:
                row.status, row.detail = "dead", "attempts_exhausted"
                return None
            token = identity()
            row.status, row.lease_token = "running", token
            row.lease_until = now() + timedelta(seconds=self.service.settings.lease_seconds)
            row.attempts += 1
            return row.id, token

    def run_one(self, job_id: str | None = None) -> bool:
        claim = self.claim(job_id)
        if not claim:
            return False
        key, token = claim
        with self.service.sessions() as s:
            row = s.get(Job, key)
            if row is None:
                return False
            tenant, kind, payload = row.tenant_id, row.kind, row.payload
        try:
            if kind == "calendar":
                receipt = self.calendar(tenant, payload["booking_id"], token, key)
            elif kind in {"crm", "followup"}:
                self.dispatch_delivery(tenant, key, token)
                return True
            else:
                raise DomainError("unknown_job_kind", 422)
            self.finish(key, token, "completed", "verified_receipt", receipt)
        except UnknownOutcome:
            self.finish(
                key,
                token,
                "reconcile" if kind == "calendar" else "unknown",
                "external_outcome_unverified",
                None,
            )
        except RetryableFailure:
            self.finish(key, token, "failed", "known_pre_send_failure", None)
        except DomainError as exc:
            self.finish(
                key,
                token,
                "superseded" if exc.code == "calendar_revision_superseded" else "dead",
                exc.code,
                None,
            )
        return True

    def dispatch_delivery(self, tenant: str, key: str, token: str) -> None:
        # Serialize dispatch with cancellation and lease recovery. Never open a
        # second transaction to finish a row locked by this transaction.
        with self.service.sessions.begin() as s:
            tenant_lock(s, tenant)
            row = s.scalar(select(Job).where(Job.id == key).with_for_update())
            if (
                not row
                or row.tenant_id != tenant
                or row.status != "running"
                or row.lease_token != token
                or row.lease_until is None
                or row.lease_until <= now()
            ):
                raise UnknownOutcome("delivery_lease_lost")
            if row.kind == "followup":
                booking = s.get(Appointment, row.payload["booking_id"])
                if (
                    not booking
                    or booking.tenant_id != tenant
                    or booking.status != "confirmed"
                    or booking.revision != row.payload["revision"]
                ):
                    row.status, row.detail = "superseded", "booking_changed"
                    row.lease_token, row.lease_until = None, None
                    audit(s, tenant, "job.superseded", key)
                    return
                receipt = self.delivery.followup(row.operation_key, row.payload)
            elif row.kind == "crm":
                receipt = self.delivery.crm(row.operation_key, row.payload, session=s)
            else:
                raise DomainError("unknown_job_kind", 422)
            row.receipt = receipt
            if row.lease_until > now():
                row.status, row.detail = "completed", "verified_receipt"
            else:
                # The receipt is retained, but crossing the lease deadline is
                # visible and must be reconciled before declaring completion.
                row.status, row.detail = "unknown", "lease_expired_after_receipt"
            row.lease_token, row.lease_until = None, None
            audit(s, tenant, "job." + row.status, key)

    def finish(self, key: str, token: str, status: str, detail: str, receipt: str | None) -> None:
        with self.service.sessions.begin() as s:
            row = s.scalar(select(Job).where(Job.id == key).with_for_update())
            if (
                not row
                or row.lease_token != token
                or row.status != "running"
                or row.lease_until is None
                or row.lease_until <= now()
            ):
                return
            row.status = (
                "dead"
                if status == "failed" and row.attempts >= self.service.settings.max_attempts
                else status
            )
            row.detail, row.receipt = detail, receipt
            row.next_run = now() + timedelta(
                seconds=self.service.settings.backoff_seconds * 2 ** (row.attempts - 1)
            )
            row.lease_token, row.lease_until = None, None
            audit(s, row.tenant_id, "job." + row.status, row.id)

    def calendar(self, tenant: str, booking_id: str, token: str, job_id: str) -> str:
        with self.service.sessions() as s:
            job = s.get(Job, job_id)
            if (
                not job
                or job.tenant_id != tenant
                or job.status != "running"
                or job.lease_token != token
                or job.lease_until is None
                or job.lease_until <= now()
            ):
                raise UnknownOutcome("lease_lost")
            row = s.get(Appointment, booking_id)
            if not row or row.tenant_id != tenant:
                raise DomainError("booking_binding_invalid", 403)
            if "intent" not in job.payload:
                raise DomainError("legacy_job_requires_reconciliation")
            payload: dict[str, Any] = job.payload["intent"]
            if row.revision != job.payload["revision"]:
                raise DomainError("calendar_revision_superseded")
            contact_details = job.payload["contact"]
        existing = self.service.calendar.get(booking_id)
        if (
            not existing
            or existing.get("status") != payload["status"]
            or (
                payload["status"] != "cancelled"
                and (
                    existing.get("start") != payload["start"]
                    or existing.get("end") != payload["end"]
                )
            )
        ):
            self.service.calendar.put(booking_id, payload)
        receipt = self.service.calendar.get(booking_id)
        if payload["status"] == "cancelled":
            if receipt and receipt.get("status") != "cancelled":
                raise UnknownOutcome("calendar_cancellation_unverified")
        else:
            from datetime import datetime

            if (
                not receipt
                or receipt.get("status") != "confirmed"
                or datetime.fromisoformat(receipt["start"])
                != datetime.fromisoformat(payload["start"])
                or datetime.fromisoformat(receipt["end"]) != datetime.fromisoformat(payload["end"])
            ):
                raise UnknownOutcome("calendar_receipt_mismatch")
        with self.service.sessions.begin() as s:
            tenant_lock(s, tenant)
            job = s.scalar(select(Job).where(Job.id == job_id).with_for_update())
            if (
                not job
                or job.lease_token != token
                or job.status != "running"
                or job.lease_until is None
                or job.lease_until < now()
            ):
                raise UnknownOutcome("lease_lost")
            row = s.get(Appointment, booking_id)
            if not row:
                raise DomainError("booking_not_found", 404)
            if row.revision != job.payload["revision"]:
                raise DomainError("calendar_revision_superseded")
            was_confirmed = row.status == "confirmed"
            row.status, row.external_id = payload["status"], booking_id
            if row.status != "cancelled":
                from datetime import datetime

                row.start = datetime.fromisoformat(payload["start"])
                row.end = datetime.fromisoformat(payload["end"])
            row.desired = None
            if row.status == "confirmed" and not was_confirmed:
                contact = s.get(Contact, row.contact_id)
                if not contact:
                    raise DomainError("contact_not_found", 404)
                followup = {
                    "booking_id": row.id,
                    **contact_details,
                    "service": row.service,
                    "revision": row.revision,
                    "start": row.start.isoformat(),
                    "timezone": self.service.business.timezone,
                }
                self.service.enqueue(s, tenant, "crm", job.operation_key, followup)
                self.service.enqueue(s, tenant, "followup", job.operation_key, followup)
            audit(s, tenant, "booking." + row.status, row.id)
        return booking_id

    def reconcile(self, tenant: str, job_id: str) -> None:
        with self.service.sessions.begin() as s:
            row = s.scalar(
                select(Job).where(Job.tenant_id == tenant, Job.id == job_id).with_for_update()
            )
            if not row:
                raise DomainError("job_not_found", 404)
            if row.kind != "calendar" or row.status not in {"reconcile", "unknown"}:
                raise DomainError("delivery_requires_provider_receipt")
            row.status, row.next_run = "pending", now()
            audit(s, tenant, "job.reconciliation.requested", row.id)
