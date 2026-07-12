import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class ResumeTailoring(Base):
    """Cached per (resume, job) tailoring result — regenerating via Groq is not
    free, so a repeat request for the same pair is served from here instead."""

    __tablename__ = "resume_tailoring"
    __table_args__ = (
        UniqueConstraint("resume_id", "job_id", name="uq_resume_job_tailoring"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"))
    resume_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resume.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job.id", ondelete="CASCADE"), nullable=False)

    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    # {"matched_keywords": [...], "missing_keywords": [...], "suggestions": [...], "summary_rewrite": "...", "gaps": [...]}
    suggestions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    tailored_text: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
