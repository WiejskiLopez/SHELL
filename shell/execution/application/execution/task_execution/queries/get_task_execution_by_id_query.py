from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetTaskExecutionByIdQuery:
    task_execution_id: str
