from __future__ import annotations

from pydantic import BaseModel


class CreateNodeExecutionResponse(BaseModel):
    id: str
