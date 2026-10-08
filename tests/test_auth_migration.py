"""Upgrade populated business rows without rewriting their payloads."""

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from sqlalchemy import inspect, select
from voicebridge.db import Base


def test_auth_migration_preserves_populated_core(app: FastAPI) -> None:
    service = app.state.service
    settings = service.settings
    engine = service.sessions.kw["bind"]
    config = Config(str(settings.migration_config))
    config.attributes["settings"] = settings
    tables = [table for table in Base.metadata.sorted_tables if table.name != "auth_sessions"]

    def rows() -> dict[str, list[dict[str, object]]]:
        with engine.connect() as connection:
            return {
                table.name: [
                    dict(row)
                    for row in connection.execute(
                        select(table).order_by(*table.primary_key.columns)
                    ).mappings()
                ]
                for table in tables
            }

    before = rows()
    assert any(before.values())
    command.downgrade(config, "0001_core")
    assert "auth_sessions" not in inspect(engine).get_table_names()
    assert rows() == before
    command.upgrade(config, "head")
    assert "auth_sessions" in inspect(engine).get_table_names()
    assert rows() == before
