from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from shell.application.execution.dto.graph_node_execution import GraphNodeExecutionDto


@dataclass(frozen=True, slots=True)
class TaskExecutionDto:
    id: str
    parent_task_execution_id: str | None = None
    name: str = ""
    version: int = 0
    hash: str = ""
    is_current: bool = True
    created_at: datetime | None = None
    body: str = ""
    work_dir: str = ""
    workflow_id: str | None = None
