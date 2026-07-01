import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base


class JobSearchResult(Base):
    __tablename__ = "job_search_result"
    __table_args__ = (
        UniqueConstraint("job_id", "search_id", name="uq_job_search"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job.id", ondelete="CASCADE"), nullable=False)
    search_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("saved_search.id", ondelete="CASCADE"), nullable=False)
    run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("search_run.id", ondelete="SET NULL"))
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False)  # Groq 1-10 normalized to 0-1
    bm25_score: Mapped[float | None] = mapped_column(Float)
    cosine_score: Mapped[float | None] = mapped_column(Float)
    is_new: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    job: Mapped["Job"] = relationship("Job", back_populates="search_results")
    saved_search: Mapped["SavedSearch"] = relationship("SavedSearch", back_populates="results")
    run: Mapped["SearchRun | None"] = relationship("SearchRun")
