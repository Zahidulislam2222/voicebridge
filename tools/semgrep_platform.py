"""Run the same fail-closed Semgrep gate on native Linux or Windows through WSL."""

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    required = {
        "ruleset",
        "scanner",
        "wsl_executable",
        "login_shell",
        "timeout_seconds",
        "path_timeout_seconds",
    }
    if set(config) != required:
        raise ValueError("Security tooling configuration keys do not match")
    for name in ("timeout_seconds", "path_timeout_seconds"):
        if type(config[name]) is not int or config[name] <= 0:
            raise ValueError("Scanner timeouts must be positive integers")
    for name in required - {"timeout_seconds", "path_timeout_seconds"}:
        if not isinstance(config[name], str) or not config[name]:
            raise ValueError("Scanner settings must be nonempty strings")
    files = []
    for name in sys.argv[2:]:
        path = Path(name).resolve(strict=True)
        if not path.is_relative_to(Path.cwd().resolve()):
            raise ValueError("Scanner file must belong to this repository")
        if sys.platform == "win32":
            result = subprocess.run(
                [config["wsl_executable"], "--exec", "wslpath", "-a", str(path)],
                check=True,
                capture_output=True,
                text=True,
                timeout=config["path_timeout_seconds"],
            )
            files.append(result.stdout.replace("\x00", "").strip())
        else:
            files.append(str(path))
    if not files:
        return 0
    args = ["scan", "--quiet", "--error", "--config", config["ruleset"], "--metrics=off", *files]
    if sys.platform == "win32":
        # The shell program is fixed protocol syntax. Filenames and scanner settings
        # are separate positional arguments, never interpolated into shell code.
        command = [
            config["wsl_executable"],
            "--exec",
            config["login_shell"],
            "-lc",
            'exec "$@"',
            "scanner",
            config["scanner"],
            *args,
        ]
    else:
        command = [config["scanner"], *args]
    return subprocess.run(command, check=False, timeout=config["timeout_seconds"]).returncode


if __name__ == "__main__":
    raise SystemExit(main())
