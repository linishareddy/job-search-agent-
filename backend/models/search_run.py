import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base


class SearchRun(Base):
    __tablename__ = "search_run"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    search_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("saved_search.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")  # running|completed|failed
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    jobs_fetched: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    jobs_matched: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_jobs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_detail: Mapped[str | None] = mapped_column(Text)

    saved_search: Mapped["SavedSearch"] = relationship("SavedSearch", back_populates="search_runs")
