"""Add indexes the UX/backend audit found missing on the original schema

Revision ID: 008
Revises: 007
Create Date: 2026-07-04

job.source is grouped on by the /health/sources endpoint with no index; the
job_search_result.run_id and notification.search_id/run_id foreign keys had no
index at all; search_run had no index supporting the scheduler's due-search
status/time filtering.

Note: applied ad hoc via main.py's startup CREATE INDEX IF NOT EXISTS (matching
this repo's existing pattern for 002-004) since Alembic has never been stamped
against the live DB. This file documents the schema history — it is not what
actually applies these indexes on this deployment.
"""

from alembic import op

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("idx_job_source", "job", ["source"])
    op.create_index("idx_jsr_run", "job_search_result", ["run_id"])
    op.create_index("idx_notification_search", "notification", ["search_id"])
    op.create_index("idx_notification_run", "notification", ["run_id"])
    op.create_index("idx_search_run_status", "search_run", ["status", "started_at"])


def downgrade() -> None:
    op.drop_index("idx_search_run_status", table_name="search_run")
    op.drop_index("idx_notification_run", table_name="notification")
    op.drop_index("idx_notification_search", table_name="notification")
    op.drop_index("idx_jsr_run", table_name="job_search_result")
    op.drop_index("idx_job_source", table_name="job")
