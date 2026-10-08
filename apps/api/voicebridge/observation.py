"""Bounded passive health sampling; probe ratios are not continuous uptime proof."""

import json
import os
import tempfile
import time
from datetime import UTC, datetime
from typing import Any

import httpx

from .settings import ObservationProfile, Settings


def record_sample(
    profile: ObservationProfile, healthy: bool, latency: float, timestamp: datetime
) -> dict[str, Any]:
    path = profile.state_file
    path.parent.mkdir(parents=True, exist_ok=True)
    state: dict[str, Any] = (
        json.loads(path.read_text())
        if path.exists()
        else {
            "started": timestamp.isoformat(),
            "samples": 0,
            "successful": 0,
            "unknown_seconds": 0.0,
            "recent": [],
            "profile_revision": profile.revision,
        }
    )
    if state["profile_revision"] != profile.revision:
        raise ValueError("Observation revision changed; preserve old evidence before restarting")
    if state.get("last_sample"):
        gap = (timestamp - datetime.fromisoformat(state["last_sample"])).total_seconds()
        if gap < 0:
            raise ValueError("Observation clock moved backward")
        if gap > profile.interval_seconds * profile.gap_factor + profile.timeout_seconds:
            state["unknown_seconds"] += gap
    state["samples"] += 1
    state["successful"] += int(healthy)
    state["last_sample"] = timestamp.isoformat()
    state["recent"] = (
        state["recent"]
        + [
            {
                "at": timestamp.isoformat(),
                "healthy": healthy,
                "latency_seconds": round(latency, 6),
            }
        ]
    )[-profile.max_recent_samples :]
    state["successful_probe_percent"] = 100 * state["successful"] / state["samples"]
    observed = (timestamp - datetime.fromisoformat(state["started"])).total_seconds()
    state["observation_seconds"] = observed
    state["required_observation_days"] = profile.observation_days
    state["target_percent"] = profile.target_percent
    state["sustained_uptime_proven"] = False
    state["limitation"] = (
        "Sampled readiness only; gaps and failures retained; continuous uptime not proven"
    )
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as target:
        json.dump(state, target, indent=2)
        target.write("\n")
        target.flush()
        os.fsync(target.fileno())
        temporary = target.name
    os.replace(temporary, path)
    return state


def observe(settings: Settings, *, once: bool = False) -> dict[str, Any]:
    profile = ObservationProfile.model_validate_json(settings.observation_file.read_text())
    with httpx.Client(
        timeout=profile.timeout_seconds, trust_env=False, follow_redirects=False
    ) as client:
        while True:
            start = time.monotonic()
            try:
                response = client.get(profile.url)
                healthy = response.status_code == profile.expected_status
                if healthy:
                    healthy = response.json().get("status") == "ready"
            except (httpx.HTTPError, ValueError, AttributeError):
                healthy = False
            result = record_sample(profile, healthy, time.monotonic() - start, datetime.now(UTC))
            if once:
                return result
            time.sleep(max(0, profile.interval_seconds - (time.monotonic() - start)))
