from __future__ import annotations

from pydantic import BaseModel


class CreateSchedulerExecutionResponse(BaseModel):
    id: str
