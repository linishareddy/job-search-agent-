import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class Resume(Base):
    __tablename__ = "resume"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Nullable: rows created before the multi-user migration are backfilled to a
    # seed user, but the column itself stays nullable so that backfill and future
    # dev-mode create_all() runs never fail on a NOT NULL without a default.
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"))
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    # pdf | docx | txt
    file_kind: Mapped[str | None] = mapped_column(String(16))
    # Relative path under backend/storage/, e.g. resumes/{id}/original.pdf
    storage_path: Mapped[str | None] = mapped_column(String(512))
    # {"skills": [...], "job_titles": [...], "experience_level": "...", "years_experience": 0, "summary": "..."}
    parsed_data: Mapped[dict | None] = mapped_column(JSONB)
    # Full structured sections: contact, summary, skills, experience[], education[], certifications[]
    parsed_sections: Mapped[dict | None] = mapped_column(JSONB)
    parse_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")  # pending|parsed|failed
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
