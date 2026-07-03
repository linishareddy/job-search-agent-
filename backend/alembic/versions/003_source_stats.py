"""Add per-source fetch stats to search_run

Revision ID: 003
Revises: 002
Create Date: 2026-07-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("search_run", sa.Column("source_stats", JSONB))


def downgrade() -> None:
    op.drop_column("search_run", "source_stats")
