from __future__ import annotations

from pydantic import BaseModel


class CreateWorkflowResponse(BaseModel):
    id: str
