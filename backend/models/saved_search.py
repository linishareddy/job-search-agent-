import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base


class SavedSearch(Base):
    __tablename__ = "saved_search"
    __table_args__ = (
        CheckConstraint("poll_interval_minutes >= 30", name="ck_poll_interval_min"),
        CheckConstraint("poll_interval_minutes <= 1440", name="ck_poll_interval_max"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    job_title: Mapped[str] = mapped_column(String(256), nullable=False)
    field_domain: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str | None] = mapped_column(String(256))
    work_mode: Mapped[str | None] = mapped_column(String(32))          # remote|hybrid|onsite|any
    experience_level: Mapped[str | None] = mapped_column(String(64))   # entry|mid|senior|lead|any
    employment_type: Mapped[str | None] = mapped_column(String(64))    # full_time|part_time|contract|any
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    # ATS company slugs: [{"name": "Stripe", "slug": "stripe", "source": "greenhouse"}, ...]
    company_slugs: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    poll_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    # Default "posted in the last N days" filter applied to /results unless overridden per-request
    posted_within_days: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Groq expansion cached here (refreshed when field_domain or job_title changes)
    field_expansion_cache: Mapped[dict | None] = mapped_column(JSONB)
    field_expansion_cached_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    search_runs: Mapped[list["SearchRun"]] = relationship("SearchRun", back_populates="saved_search", cascade="all, delete-orphan")
    results: Mapped[list["JobSearchResult"]] = relationship("JobSearchResult", back_populates="saved_search", cascade="all, delete-orphan")
    notifications: Mapped[list["Notification"]] = relationship("Notification", back_populates="saved_search")
