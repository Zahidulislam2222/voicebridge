import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from voicebridge import cli


def test_migration_configuration_path_comes_from_settings(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    expected = tmp_path / "configured-migrations.ini"
    settings = app.state.service.settings.model_copy(update={"migration_config": expected})
    observed = []
    monkeypatch.setattr(cli, "load_settings", lambda _: settings)
    monkeypatch.setattr(
        cli.command, "upgrade", lambda config, _: observed.append(config.config_file_name)
    )
    monkeypatch.setattr(sys, "argv", ["voicebridge", "migrate", "--env-file", "test-only-env-path"])
    cli.main()
    assert observed == [str(expected)]
