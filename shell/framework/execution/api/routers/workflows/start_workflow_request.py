from __future__ import annotations

from pydantic import BaseModel


class StartWorkflowRequest(BaseModel):
    task_execution_id: str
