"""Add current_stage_index to search_run for real pipeline-progress polling

Revision ID: 007
Revises: 006
Create Date: 2026-07-04

Note: applied ad hoc via main.py's startup ALTER TABLE (matching this repo's
existing pattern for 002-004) since Alembic has never been stamped against the
live DB. This file documents the schema history — it is not what actually
applies the column on this deployment.
"""

from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "search_run",
        sa.Column("current_stage_index", sa.Integer, nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("search_run", "current_stage_index")
