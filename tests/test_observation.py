from datetime import UTC, datetime, timedelta
from pathlib import Path

from voicebridge.observation import record_sample
from voicebridge.settings import ObservationProfile


def test_observation_preserves_failures_gaps_and_bounded_history(tmp_path: Path) -> None:
    profile = ObservationProfile.model_validate_json(
        Path("config/observation-profiles.json").read_text()
    )
    profile = profile.model_copy(
        update={"state_file": tmp_path / "observation.json", "max_recent_samples": 2}
    )
    start = datetime.now(UTC)
    record_sample(profile, True, 0.01, start)
    record_sample(profile, False, 0.02, start + timedelta(seconds=60))
    state = record_sample(profile, True, 0.01, start + timedelta(seconds=360))
    assert state["samples"] == 3
    assert state["successful"] == 2
    assert state["unknown_seconds"] == 300
    assert len(state["recent"]) == 2
    assert state["sustained_uptime_proven"] is False
    assert 66 < state["successful_probe_percent"] < 67
