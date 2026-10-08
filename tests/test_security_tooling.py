"""Publication tooling must preserve findings and pass paths as separate arguments."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "semgrep_platform", ROOT / "tools/semgrep_platform.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Security adapter cannot be loaded")
ADAPTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADAPTER)


def prepare(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "settings.json").write_bytes((ROOT / "config/security-tooling.json").read_bytes())
    file = tmp_path / "input.py"
    file.write_text("value = 1\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(ADAPTER.sys, "argv", ["scanner", "settings.json", "input.py"])
    return file


def test_native_findings_are_not_ignored(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    file = prepare(tmp_path, monkeypatch)
    monkeypatch.setattr(ADAPTER.sys, "platform", "linux")
    run = Mock(return_value=SimpleNamespace(returncode=1))
    monkeypatch.setattr(ADAPTER.subprocess, "run", run)
    assert ADAPTER.main() == 1
    assert run.call_args.args[0][-1] == str(file)
    assert run.call_args.kwargs["check"] is False


def test_windows_paths_are_positional(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prepare(tmp_path, monkeypatch)
    monkeypatch.setattr(ADAPTER.sys, "platform", "win32")
    converted = "/converted/input with $characters.py"
    run = Mock(
        side_effect=[SimpleNamespace(stdout=converted + "\n"), SimpleNamespace(returncode=2)]
    )
    monkeypatch.setattr(ADAPTER.subprocess, "run", run)
    assert ADAPTER.main() == 2
    command = run.call_args.args[0]
    assert command[4] == 'exec "$@"'
    assert command[-1] == converted
    assert converted not in command[4]


def test_invalid_timeout_fails_before_scanner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare(tmp_path, monkeypatch)
    config = json.loads(Path("settings.json").read_text())
    config["timeout_seconds"] = True
    Path("settings.json").write_text(json.dumps(config))
    with pytest.raises(ValueError, match="positive integers"):
        ADAPTER.main()


def test_outside_repository_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prepare(tmp_path, monkeypatch)
    monkeypatch.setattr(ADAPTER.sys, "argv", ["scanner", "settings.json", str(ROOT / "README.md")])
    with pytest.raises(ValueError, match="belong to this repository"):
        ADAPTER.main()
