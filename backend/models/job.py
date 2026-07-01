import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base


class Job(Base):
    __tablename__ = "job"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Exact dedup key: SHA256(normalize(company) + "|" + normalize(title))
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    # All source URLs where this job was found (merged from duplicates)
    source_urls: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    company_name: Mapped[str] = mapped_column(String(256), nullable=False)
    location: Mapped[str | None] = mapped_column(String(256))
    work_mode: Mapped[str | None] = mapped_column(String(32))          # remote|hybrid|onsite|unknown
    employment_type: Mapped[str | None] = mapped_column(String(64))
    experience_level: Mapped[str | None] = mapped_column(String(64))

    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    salary_currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    salary_listed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    description_raw: Mapped[str | None] = mapped_column(Text)
    description_summary: Mapped[str | None] = mapped_column(String(1024))  # Groq-generated
    skills: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    apply_url: Mapped[str] = mapped_column(Text, nullable=False)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # all-MiniLM-L6-v2 produces 384-dim vectors
    embedding: Mapped[list | None] = mapped_column(Vector(384))

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    search_results: Mapped[list["JobSearchResult"]] = relationship("JobSearchResult", back_populates="job", cascade="all, delete-orphan")
