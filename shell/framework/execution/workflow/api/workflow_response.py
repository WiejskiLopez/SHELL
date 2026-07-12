from __future__ import annotations

from pydantic import BaseModel


class WorkflowResponse(BaseModel):
    workflow_id: str
    status: str
    session_id: str | None = None
    created_at: str | None = None
