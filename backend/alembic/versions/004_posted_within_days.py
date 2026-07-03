"""Add posted_within_days time-period filter to saved_search

Revision ID: 004
Revises: 003
Create Date: 2026-07-03
"""

from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("saved_search", sa.Column("posted_within_days", sa.Integer))


def downgrade() -> None:
    op.drop_column("saved_search", "posted_within_days")
