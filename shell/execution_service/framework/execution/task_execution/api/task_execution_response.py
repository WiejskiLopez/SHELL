from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TaskExecutionResponse(BaseModel):
    id: str
    name: str
    work_dir: str
    workflow_id: str
    created_at: datetime
    changed_at: datetime | None = None
    deleted_at: datetime | None = None
