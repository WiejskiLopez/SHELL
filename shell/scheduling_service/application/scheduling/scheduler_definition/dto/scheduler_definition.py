from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from shell.scheduling_service.application.scheduling.scheduler_definition.dto.action_config_dto import (
    ActionConfigDto,
)
from shell.scheduling_service.application.scheduling.scheduler_definition.dto.execution_policy_dto import (
    ExecutionPolicyDto,
)


@dataclass(frozen=True, slots=True)
class SchedulerDefinitionDto:
    id: str
    name: str
    created_at: datetime
    description: str | None = None
    source_context: str = ""
    trigger_event_type: str = ""
    trigger_filter: str | None = None
    action_type: str = ""
    action_config: ActionConfigDto | None = None
    execution_policy: ExecutionPolicyDto | None = None
    enabled: bool = True
    changed_at: datetime | None = None
