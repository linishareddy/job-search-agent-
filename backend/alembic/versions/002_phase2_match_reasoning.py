"""Phase 2: add match_reason/gaps to job_search_result

Revision ID: 002
Revises: 001
Create Date: 2026-07-02
"""

from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job_search_result", sa.Column("match_reason", sa.Text))
    op.add_column("job_search_result", sa.Column("gaps", sa.Text))


def downgrade() -> None:
    op.drop_column("job_search_result", "gaps")
    op.drop_column("job_search_result", "match_reason")
