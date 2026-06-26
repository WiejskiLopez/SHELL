from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class TaskExecutionStateDto:
    id: str
    task_execution_id: str
    kind: str
    payload: dict[str, Any]
    is_current: bool
    created_at: datetime
