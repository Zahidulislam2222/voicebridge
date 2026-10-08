import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import insert
from voicebridge.db import Contact
from voicebridge.settings import Settings

from .test_http_providers_knowledge import headers


def test_current_api_matches_reviewable_openapi_artifact(app: FastAPI) -> None:
    assert app.openapi() == json.loads(Path("docs/api/core-openapi.json").read_text())


def test_environment_coverage_and_no_business_provider_literals() -> None:
    example = Path(".env.example").read_text()
    for field in Settings.model_fields:
        if field == "provider":
            from voicebridge.settings import ProviderSettings

            for nested in ProviderSettings.model_fields:
                assert "VB_PROVIDER__" + nested.upper() + "=" in example
        else:
            assert "VB_" + field.upper() + "=" in example
    for file in Path("apps/api/voicebridge").glob("*.py"):
        text = file.read_text()
        assert not re.search(
            r"https?://|(?:sk-proj-|sk-or-v1-)[A-Za-z0-9_-]{12,}|-----BEGIN .*PRIVATE KEY", text
        )


def sample_resources() -> tuple[int, int, int]:
    cpu = list(map(int, Path("/proc/stat").read_text().splitlines()[0].split()[1:]))
    mem = {
        line.split(":")[0]: int(line.split()[1])
        for line in Path("/proc/meminfo").read_text().splitlines()
        if len(line.split()) >= 2
    }
    return sum(cpu), cpu[3] + cpu[4], round((1 - mem["MemAvailable"] / mem["MemTotal"]) * 100)


def test_bounded_core_capacity_and_health(app: FastAPI) -> None:
    profile = json.loads(Path("config/capacity-profiles.json").read_text())["local"]
    total, idle, memory = sample_resources()
    if memory >= profile["memory_stop_percent"]:
        import pytest

        pytest.skip("Resource guard refused load: host memory busy")
    rows = [
        {
            "id": "capacity-" + str(i),
            "tenant_id": "northline",
            "name": "Synthetic capacity contact",
            "email": "capacity-" + str(i) + "@voicebridge.invalid",
            "phone": "+15555550123",
            "notes": "",
        }
        for i in range(profile["seed_rows"])
    ]
    with app.state.service.sessions.begin() as s:
        s.execute(insert(Contact), rows)
    started = time.perf_counter()
    results = []
    observations = []
    stopped = None

    def visit(_: int) -> tuple[int, float, int]:
        with TestClient(app) as c:
            begin = time.perf_counter()
            response = c.get("/api/state", headers=headers(app))
            duration = time.perf_counter() - begin
            assert (
                len(response.json()["contacts"]) <= app.state.service.settings.max_records_per_page
            )
            health = c.get("/health/ready").status_code
            return response.status_code, duration, health

    with ThreadPoolExecutor(max_workers=profile["concurrency"]) as pool:
        for offset in range(0, profile["requests"], profile["concurrency"]):
            if time.perf_counter() - started > profile["max_duration_seconds"]:
                stopped = "duration_guard"
                break
            batch = list(
                pool.map(
                    visit, range(offset, min(offset + profile["concurrency"], profile["requests"]))
                )
            )
            results.extend(batch)
            time.sleep(profile["concurrency"] / profile["requests_per_second"])
            current, current_idle, memory = sample_resources()
            cpu_percent = 100 * (1 - (current_idle - idle) / max(1, current - total))
            observations.append({"cpu_percent": round(cpu_percent, 2), "memory_percent": memory})
            total, idle = current, current_idle
            if (
                cpu_percent >= profile["cpu_stop_percent"]
                or memory >= profile["memory_stop_percent"]
            ):
                stopped = "resource_guard"
                break
            if any(
                status != 200 or health != 200 or duration > profile["max_response_seconds"]
                for status, duration, health in batch
            ):
                stopped = "response_guard"
                break
    latencies = sorted(row[1] for row in results)
    errors = sum(status != 200 or health != 200 for status, _, health in results)
    elapsed = time.perf_counter() - started
    evidence = {
        "profile_revision": 1,
        "synthetic_contacts": len(rows),
        "concurrency_cap": profile["concurrency"],
        "requests": len(results),
        "errors": errors,
        "elapsed_seconds": round(elapsed, 3),
        "request_rate": round(len(results) / elapsed, 3),
        "p95_seconds": round(latencies[max(0, int(len(latencies) * 0.95) - 1)], 4),
        "max_seconds": round(max(latencies), 4),
        "health_observations": len(results),
        "resource_observations": observations,
        "stopped": stopped,
        "paid_requests": 0,
        "million_users_proven": False,
        "long_window_uptime_proven": False,
        "hardware_logical_cpus": os.cpu_count(),
    }
    Path(".local/evidence/core-capacity.json").write_text(json.dumps(evidence, indent=2) + "\n")
    assert stopped is None, evidence
    assert errors <= profile["max_errors"]
