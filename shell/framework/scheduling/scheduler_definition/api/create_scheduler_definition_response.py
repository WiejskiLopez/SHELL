from __future__ import annotations

from pydantic import BaseModel


class CreateSchedulerDefinitionResponse(BaseModel):
    id: str
