"""A clean CI environment must declare dependencies used by real recovery tests."""

from pathlib import Path

import yaml
from voicebridge.settings import load_settings

ROOT = Path(__file__).resolve().parents[1]


def test_ci_has_capture_smtp_matching_the_safe_environment() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/quality.yml").read_text())
    backend = workflow["jobs"]["backend"]
    capture = backend["services"]["mailpit"]
    settings = load_settings(ROOT / ".env.example")
    assert settings.smtp_host == "127.0.0.1"
    assert any(int(port.split(":")[0]) == settings.smtp_port for port in capture["ports"])
    assert "@sha256:" in capture["image"]
    assert not any("RELAY" in key for key in capture.get("env", {}))
    assert not settings.provider.enabled
    assert settings.followup_transport == "capture"


def test_ci_bootstrap_creates_the_suite_output_directory() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/quality.yml").read_text())
    steps = workflow["jobs"]["backend"]["steps"]
    setup = next(step["run"] for step in steps if step.get("name") == "Isolated test environment")
    assert "mkdir -p .local/core-engine .local/evidence" in setup
    assert "cp .env.example .local/core-engine/.env" in setup
