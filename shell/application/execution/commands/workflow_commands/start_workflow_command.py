from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StartWorkflowCommand:
    task_execution_id: str

    def __post_init__(self) -> None:
        if not self.task_execution_id:
            raise ValueError("task_execution_id cannot be empty")
