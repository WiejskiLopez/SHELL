from __future__ import annotations

from pydantic import BaseModel


class CreateWorkflowRequest(BaseModel):
    session_id: str | None = None
