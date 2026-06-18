from __future__ import annotations

from pydantic import BaseModel


class ImportTaskResponse(BaseModel):
    task_execution_id: str
