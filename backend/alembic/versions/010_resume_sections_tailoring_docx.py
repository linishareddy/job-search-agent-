"""Resume structured sections, file storage, and DOCX tailoring artifacts

Revision ID: 010
Revises: 009
Create Date: 2026-07-12

Adds parsed_sections + file storage columns on resume, tailored_sections +
docx_path on resume_tailoring, and tailored_docx_path on job_application.

Note: applied ad hoc via main.py's startup ALTER TABLE IF NOT EXISTS block.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("resume", sa.Column("file_kind", sa.String(16)))
    op.add_column("resume", sa.Column("storage_path", sa.String(512)))
    op.add_column("resume", sa.Column("parsed_sections", JSONB))

    op.add_column("resume_tailoring", sa.Column("tailored_sections", JSONB))
    op.add_column("resume_tailoring", sa.Column("docx_path", sa.String(512)))
    op.add_column("resume_tailoring", sa.Column("template_id", sa.String(64), server_default="classic"))

    op.add_column("job_application", sa.Column("tailored_docx_path", sa.String(512)))


def downgrade() -> None:
    op.drop_column("job_application", "tailored_docx_path")
    op.drop_column("resume_tailoring", "template_id")
    op.drop_column("resume_tailoring", "docx_path")
    op.drop_column("resume_tailoring", "tailored_sections")
    op.drop_column("resume", "parsed_sections")
    op.drop_column("resume", "storage_path")
    op.drop_column("resume", "file_kind")
