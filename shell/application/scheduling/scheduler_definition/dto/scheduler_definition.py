from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class SchedulerDefinitionDto:
    id: str
    name: str
    description: str | None = None
    source_context: str = ""
    trigger_event_type: str = ""
    trigger_filter: dict[str, Any] | None = None
    action_type: str = ""
    action_config: dict[str, Any] | None = None
    execution_policy: dict[str, Any] | None = None
    enabled: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
