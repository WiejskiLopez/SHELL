from __future__ import annotations

from pydantic import BaseModel


class StartWorkflowResponse(BaseModel):
    workflow_id: str
