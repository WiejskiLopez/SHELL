from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from shell.execution_service.application.execution.node_execution.dto.node_execution import (
    NodeExecutionDto,
)


@dataclass(frozen=True, slots=True)
class TaskExecutionDto:
    id: str
    created_at: datetime
    name: str = ""
    work_dir: str = ""
    workflow_id: str = ""
    changed_at: datetime | None = None
    deleted_at: datetime | None = None
    node_executions: tuple[NodeExecutionDto, ...] = field(default_factory=tuple)
