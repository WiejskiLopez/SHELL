from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class TaskExecutionDto:
    id: str
    name: str = ""
    body: str = ""
    created_at: datetime | None = None
    work_dir: str = ""
    workflow_id: str | None = None
    graph_node_executions: tuple[Any, ...] = field(default_factory=tuple)
