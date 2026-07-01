import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    search_id: Optional[uuid.UUID]
    run_id: Optional[uuid.UUID]
    message: str
    new_job_count: int
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}
