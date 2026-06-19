from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class TaskExecutionInputPayloadDto:
    id: str
    task_execution_id: str
    payload: dict
    is_current: bool
    created_at: datetime
