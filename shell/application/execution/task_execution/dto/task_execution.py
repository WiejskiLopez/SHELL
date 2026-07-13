from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class TaskExecutionDto:
    id: str
    name: str = ""
    body: str = ""
    created_at: datetime | None = None
    work_dir: str = ""
    workflow_id: str | None = None
    node_executions: tuple[Any, ...] = field(default_factory=tuple)
