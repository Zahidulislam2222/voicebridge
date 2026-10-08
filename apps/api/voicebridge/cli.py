"""Local processes; a worker lives independently of the HTTP request lifecycle."""

import argparse
import json
import time
from pathlib import Path

import uvicorn
from alembic import command
from alembic.config import Config

from .api import create_app
from .observation import observe
from .settings import load_settings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=[
            "migrate",
            "seed",
            "api",
            "worker",
            "worker-once",
            "openapi",
            "observe",
            "observe-once",
        ],
    )
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    settings = load_settings(args.env_file)
    if args.action in {"observe", "observe-once"}:
        result = observe(settings, once=args.action == "observe-once")
        print(
            json.dumps(
                {key: result[key] for key in ("samples", "successful", "sustained_uptime_proven")}
            )
        )
        return
    if args.action == "migrate":
        config = Config(str(settings.migration_config))
        config.attributes["settings"] = settings
        command.upgrade(config, "head")
        return
    app = create_app(settings)
    if args.action == "seed":
        app.state.service.seed(settings.tenant_id)
    elif args.action == "api":
        uvicorn.run(app, host=settings.host, port=settings.port, access_log=False)
    elif args.action == "worker-once":
        app.state.worker.run_one()
    elif args.action == "worker":
        try:
            while True:
                if not app.state.worker.run_one():
                    time.sleep(settings.worker_poll_seconds)
        except KeyboardInterrupt:
            return
    elif args.output:
        args.output.write_text(json.dumps(app.openapi(), indent=2) + "\n")
    else:
        parser.error("openapi requires --output")


if __name__ == "__main__":
    main()
