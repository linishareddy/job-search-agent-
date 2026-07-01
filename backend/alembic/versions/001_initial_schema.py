"""Initial schema with pgvector

Revision ID: 001
Revises:
Create Date: 2026-07-01
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "user",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("display_name", sa.String(100)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "saved_search",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("job_title", sa.String(256), nullable=False),
        sa.Column("field_domain", sa.Text, nullable=False),
        sa.Column("location", sa.String(256)),
        sa.Column("work_mode", sa.String(32)),
        sa.Column("experience_level", sa.String(64)),
        sa.Column("employment_type", sa.String(64)),
        sa.Column("salary_min", sa.Integer),
        sa.Column("salary_max", sa.Integer),
        sa.Column("company_slugs", JSONB, nullable=False, server_default="[]"),
        sa.Column("poll_interval_minutes", sa.Integer, nullable=False, server_default="60"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("last_run_at", sa.DateTime(timezone=True)),
        sa.Column("field_expansion_cache", JSONB),
        sa.Column("field_expansion_cached_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("poll_interval_minutes >= 30", name="ck_poll_interval_min"),
        sa.CheckConstraint("poll_interval_minutes <= 1440", name="ck_poll_interval_max"),
    )
    op.create_index("idx_saved_search_user", "saved_search", ["user_id"])
    op.create_index("idx_saved_search_active", "saved_search", ["is_active"], postgresql_where=sa.text("is_active = TRUE"))

    op.create_table(
        "ats_company",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("slug", "source", name="uq_ats_company_slug_source"),
    )

    op.create_table(
        "job",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("fingerprint", sa.String(64), nullable=False, unique=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("source_urls", JSONB, nullable=False, server_default="[]"),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("company_name", sa.String(256), nullable=False),
        sa.Column("location", sa.String(256)),
        sa.Column("work_mode", sa.String(32)),
        sa.Column("employment_type", sa.String(64)),
        sa.Column("experience_level", sa.String(64)),
        sa.Column("salary_min", sa.Integer),
        sa.Column("salary_max", sa.Integer),
        sa.Column("salary_currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("salary_listed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("description_raw", sa.Text),
        sa.Column("description_summary", sa.String(1024)),
        sa.Column("skills", JSONB, nullable=False, server_default="[]"),
        sa.Column("apply_url", sa.Text, nullable=False),
        sa.Column("posted_at", sa.DateTime(timezone=True)),
        sa.Column("embedding", Vector(384)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_job_fingerprint", "job", ["fingerprint"], unique=True)
    op.create_index("idx_job_posted", "job", ["posted_at"], postgresql_using="btree")
    op.create_index("idx_job_company", "job", ["company_name"])
    op.execute(
        "CREATE INDEX idx_job_embedding ON job USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    op.create_table(
        "search_run",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("search_id", UUID(as_uuid=True), sa.ForeignKey("saved_search.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("jobs_fetched", sa.Integer, nullable=False, server_default="0"),
        sa.Column("jobs_matched", sa.Integer, nullable=False, server_default="0"),
        sa.Column("new_jobs", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_detail", sa.Text),
    )
    op.create_index("idx_search_run_search", "search_run", ["search_id"])

    op.create_table(
        "job_search_result",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", UUID(as_uuid=True), sa.ForeignKey("job.id", ondelete="CASCADE"), nullable=False),
        sa.Column("search_id", UUID(as_uuid=True), sa.ForeignKey("saved_search.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("search_run.id", ondelete="SET NULL")),
        sa.Column("relevance_score", sa.Float, nullable=False),
        sa.Column("bm25_score", sa.Float),
        sa.Column("cosine_score", sa.Float),
        sa.Column("is_new", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_dismissed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("job_id", "search_id", name="uq_job_search"),
    )
    op.create_index("idx_jsr_search_score", "job_search_result", ["search_id", "relevance_score"])
    op.create_index(
        "idx_jsr_new", "job_search_result", ["search_id", "is_new"],
        postgresql_where=sa.text("is_new = TRUE"),
    )

    op.create_table(
        "notification",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("search_id", UUID(as_uuid=True), sa.ForeignKey("saved_search.id", ondelete="SET NULL")),
        sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("search_run.id", ondelete="SET NULL")),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("new_job_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_notification_user", "notification", ["user_id", "is_read"])


def downgrade() -> None:
    op.drop_table("notification")
    op.drop_table("job_search_result")
    op.drop_table("search_run")
    op.drop_table("job")
    op.drop_table("ats_company")
    op.drop_table("saved_search")
    op.drop_table("user")
    op.execute("DROP EXTENSION IF EXISTS vector")
