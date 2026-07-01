import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base


class Notification(Base):
    __tablename__ = "notification"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    search_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("saved_search.id", ondelete="SET NULL"))
    run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("search_run.id", ondelete="SET NULL"))
    message: Mapped[str] = mapped_column(Text, nullable=False)
    new_job_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="notifications")
    saved_search: Mapped["SavedSearch | None"] = relationship("SavedSearch", back_populates="notifications")
