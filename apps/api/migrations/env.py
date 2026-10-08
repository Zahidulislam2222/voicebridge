"""Migration URL is obtained only from the typed secret configuration."""

from alembic import context
from sqlalchemy import create_engine
from voicebridge.db import Base

settings = context.config.attributes["settings"]
engine = create_engine(settings.database_url.get_secret_value(), hide_parameters=True)
with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
