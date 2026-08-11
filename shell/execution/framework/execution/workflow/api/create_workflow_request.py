from __future__ import annotations

from pydantic import BaseModel


class CreateWorkflowRequest(BaseModel):
    session_id: str
    project_id: str
