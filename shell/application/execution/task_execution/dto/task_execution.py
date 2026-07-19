from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from shell.application.execution.node_execution.dto.node_execution import NodeExecutionDto


@dataclass(frozen=True, slots=True)
class TaskExecutionDto:
    id: str
    name: str = ""
    created_at: datetime | None = None
    work_dir: str = ""
    workflow_id: str | None = None
    node_executions: tuple[NodeExecutionDto, ...] = field(default_factory=tuple)
