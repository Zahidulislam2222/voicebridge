"""Opaque encrypted server sessions; preserve populated core schema."""

import sqlalchemy as sa
from alembic import op

revision = "0002_auth_sessions"
down_revision = "0001_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auth_sessions",
        sa.Column("digest", sa.String(64), primary_key=True),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("tenant_id", sa.String(100), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("expires", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_auth_sessions_tenant_id", "auth_sessions", ["tenant_id"])
    op.create_index("ix_auth_sessions_expires", "auth_sessions", ["expires"])
    op.create_index("ix_auth_sessions_kind", "auth_sessions", ["kind"])


def downgrade() -> None:
    op.drop_table("auth_sessions")
