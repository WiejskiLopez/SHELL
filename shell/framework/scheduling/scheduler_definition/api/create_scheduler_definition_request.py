from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreateSchedulerDefinitionRequest(BaseModel):
    name: str = Field(..., min_length=1)
    trigger_config: dict[str, Any]
    action_config: dict[str, Any]
    execution_policy: dict[str, Any]
    enabled: bool = True
    description: str | None = None
