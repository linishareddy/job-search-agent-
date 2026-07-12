"""Add multi-user auth, resume tailoring, and assisted auto-apply

Revision ID: 009
Revises: 008
Create Date: 2026-07-09

Adds the `user` table (auth + notification/auto-apply preferences) and
`resume_tailoring` table (cached per resume/job tailoring results), attaches
`user_id` ownership to `resume`, `saved_search`, and `job_application`, and adds
auto-apply artifact columns (auto_prepared, match_score, cover_letter,
tailored_resume) to `job_application`. job_application's unique constraint moves
from unique(job_id) to unique(user_id, job_id) so two users can independently
track the same job.

Note: applied ad hoc via main.py's startup ALTER TABLE IF NOT EXISTS block
(matching this repo's existing pattern for 002-004, 007-008) since Alembic has
never been stamped against the live DB. That startup block also seeds a default
user and backfills pre-existing rows onto it. This file documents the schema
history — it is not what actually applies these changes on this deployment.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("name", sa.String(256)),
        sa.Column("hashed_password", sa.String(256), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("email_enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("auto_apply_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("auto_apply_min_score", sa.Float, nullable=False, server_default="0.7"),
        sa.Column("auto_apply_resume_id", UUID(as_uuid=True), sa.ForeignKey("resume.id", ondelete="SET NULL")),
        sa.Column("auto_apply_max_per_run", sa.Integer, nullable=False, server_default="5"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.add_column("resume", sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="CASCADE")))
    op.add_column("saved_search", sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="CASCADE")))
    op.add_column("job_application", sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="CASCADE")))
    op.add_column("job_application", sa.Column("auto_prepared", sa.Boolean, nullable=False, server_default="false"))
    op.add_column("job_application", sa.Column("match_score", sa.Float))
    op.add_column("job_application", sa.Column("cover_letter", sa.Text))
    op.add_column("job_application", sa.Column("tailored_resume", sa.Text))

    op.drop_constraint("job_application_job_id_key", "job_application", type_="unique")
    op.create_unique_constraint("uq_user_job_application", "job_application", ["user_id", "job_id"])

    op.create_table(
        "resume_tailoring",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="CASCADE")),
        sa.Column("resume_id", UUID(as_uuid=True), sa.ForeignKey("resume.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", UUID(as_uuid=True), sa.ForeignKey("job.id", ondelete="CASCADE"), nullable=False),
        sa.Column("match_score", sa.Float, nullable=False),
        sa.Column("suggestions", JSONB, nullable=False, server_default="{}"),
        sa.Column("tailored_text", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("resume_id", "job_id", name="uq_resume_job_tailoring"),
    )


def downgrade() -> None:
    op.drop_table("resume_tailoring")
    op.drop_constraint("uq_user_job_application", "job_application", type_="unique")
    op.create_unique_constraint("job_application_job_id_key", "job_application", ["job_id"])
    op.drop_column("job_application", "tailored_resume")
    op.drop_column("job_application", "cover_letter")
    op.drop_column("job_application", "match_score")
    op.drop_column("job_application", "auto_prepared")
    op.drop_column("job_application", "user_id")
    op.drop_column("saved_search", "user_id")
    op.drop_column("resume", "user_id")
    op.drop_table("user")
