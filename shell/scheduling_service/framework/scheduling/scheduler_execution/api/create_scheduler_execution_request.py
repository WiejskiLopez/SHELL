from __future__ import annotations

from pydantic import BaseModel


class CreateSchedulerExecutionRequest(BaseModel):
    scheduler_definition_id: str
