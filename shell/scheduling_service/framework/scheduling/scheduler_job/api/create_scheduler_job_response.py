from __future__ import annotations

from pydantic import BaseModel


class CreateSchedulerJobResponse(BaseModel):
    id: str
