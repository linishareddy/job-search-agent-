import uuid
from typing import Optional

from pydantic import BaseModel


class RunStatusResponse(BaseModel):
    run_id: uuid.UUID
    status: str  # running|completed|failed
    current_stage_index: int
    current_stage_label: str
    total_stages: int
    jobs_fetched: int
    jobs_matched: int
    new_jobs: int
    error_detail: Optional[str] = None
