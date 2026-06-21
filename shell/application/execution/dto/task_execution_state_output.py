from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class TaskExecutionStateOutputDto:
    id: str
    task_execution_id: str
    payload: dict[str, Any]
    is_current: bool
    created_at: datetime
