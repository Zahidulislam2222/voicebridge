"""Kill only owned fixture processes; exercise the actual CLI worker loop."""

import multiprocessing
import signal
import sys
import time
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi import FastAPI
from sqlalchemy import select
from voicebridge import cli
from voicebridge.connectors import Delivery, LocalCalendar
from voicebridge.db import ExternalRecord, Job, now
from voicebridge.settings import Settings

from tests.test_booking_engine import request


def worker_process(settings: Settings, pause_kind: str, reached: Any, sends: Any) -> None:
    # Only configuration injection is test-specific. Run the real CLI loop,
    # database claims, connector effects and completion logic in a new process.
    cli.load_settings = lambda _: settings
    original_put, original_followup = LocalCalendar.put, Delivery.followup

    def put(self: LocalCalendar, key: str, payload: dict[str, Any]) -> str:
        result = original_put(self, key, payload)
        if pause_kind == "calendar":
            reached.set()
            signal.pause()
        return result

    def followup(self: Delivery, key: str, payload: dict[str, Any]) -> str:
        with sends.get_lock():
            sends.value += 1
        receipt = original_followup(self, key, payload)
        if pause_kind == "followup":
            reached.set()
            signal.pause()
        return receipt

    LocalCalendar.put, Delivery.followup = put, followup
    sys.argv = ["voicebridge", "worker", "--env-file", "fixture-settings-injected"]
    cli.main()


def await_status(app: FastAPI, key: str, expected: str, timeout: float = 12) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with app.state.service.sessions() as session:
            if session.get(Job, key).status == expected:
                return
        time.sleep(0.05)
    pytest.fail(f"Owned fixture job did not reach {expected}")


@pytest.mark.parametrize("pause_kind", ["calendar", "followup"])
def test_cli_worker_process_death_and_restart(app: FastAPI, pause_kind: str) -> None:
    context = multiprocessing.get_context("fork")
    settings = app.state.service.settings.model_copy(
        update={"lease_seconds": 2, "worker_poll_seconds": 0.05}
    )
    reached, sends = context.Event(), context.Value("i", 0)
    booking = app.state.service.book(settings.tenant_id, request(app, "crash-" + pause_kind))
    if pause_kind == "followup":
        app.state.providers.drain_calendar(settings.tenant_id, booking["booking_id"])
    with app.state.service.sessions() as session:
        key = session.scalar(select(Job.id).where(Job.kind == pause_kind))
    assert key is not None
    crashed = context.Process(target=worker_process, args=(settings, pause_kind, reached, sends))
    restarted = context.Process(target=worker_process, args=(settings, "", reached, sends))
    try:
        crashed.start()
        assert reached.wait(12), "Test worker did not reach its committed external effect"
        with app.state.service.sessions() as session:
            job = session.get(Job, key)
            assert job.status == "running" and job.lease_until is not None
            lease_deadline = job.lease_until
        crashed.kill()
        crashed.join(5)
        assert crashed.exitcode == -signal.SIGKILL
        # Let the actual lease expire; do not manufacture expiry in the DB.
        remaining = (lease_deadline - now()).total_seconds()
        if remaining > 0:
            time.sleep(remaining + 0.1)
        restarted.start()
        await_status(app, key, "completed" if pause_kind == "calendar" else "unknown")
        time.sleep(0.2)
        with app.state.service.sessions() as session:
            job = session.get(Job, key)
            assert job.attempts == (2 if pause_kind == "calendar" else 1)
            events = list(
                session.scalars(select(ExternalRecord).where(ExternalRecord.kind == "calendar"))
            )
            assert len(events) == 1 and events[0].id == booking["booking_id"]
        assert (
            app.state.service.appointment(settings.tenant_id, booking["booking_id"])["status"]
            == "confirmed"
        )
        if pause_kind == "followup":
            assert sends.value == 1, "Unknown SMTP delivery must never be resent automatically"
        import json
        from pathlib import Path

        target = Path(".local/evidence") / ("core-worker-crash-" + pause_kind + ".json")
        target.write_text(
            json.dumps(
                {
                    "checked_at": datetime.now(UTC).isoformat(),
                    "effect": pause_kind,
                    "actual_cli_process": True,
                    "configuration_injected_from_isolated_fixture": True,
                    "killed_exit_code": crashed.exitcode,
                    "real_lease_expiry": True,
                    "restart_outcome": "completed" if pause_kind == "calendar" else "unknown",
                    "single_calendar_event": True,
                    "smtp_attempts": sends.value,
                    "paid_provider_requests": 0,
                },
                indent=2,
            )
            + "\n"
        )
    finally:
        for process in (crashed, restarted):
            if process.pid is not None and process.is_alive():
                process.terminate()
                process.join(5)
            if process.pid is not None and process.is_alive():
                process.kill()
                process.join(5)
