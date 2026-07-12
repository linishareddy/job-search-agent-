import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base


class JobApplication(Base):
    __tablename__ = "job_application"
    __table_args__ = (
        # Ownership moved from a single-tenant unique(job_id) to unique(user_id, job_id)
        # so two users can each independently track/auto-apply to the same job.
        UniqueConstraint("user_id", "job_id", name="uq_user_job_application"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Nullable for the same backfill reason as Resume.user_id.
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"))
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="saved")  # saved|ready_to_apply|applied|interviewing|offer|rejected
    notes: Mapped[str | None] = mapped_column(Text)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Auto-apply artifacts — populated when this card was prepared by the auto-apply
    # scheduler rather than created manually via the tracker UI.
    auto_prepared: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    match_score: Mapped[float | None] = mapped_column(Float)
    cover_letter: Mapped[str | None] = mapped_column(Text)
    tailored_resume: Mapped[str | None] = mapped_column(Text)
    # Relative path to generated tailored DOCX under backend/storage/
    tailored_docx_path: Mapped[str | None] = mapped_column(String(512))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    job: Mapped["Job"] = relationship("Job")
