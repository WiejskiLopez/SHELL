from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RunTaskerWorkflowCommand:
    task_execution_id: str
    work_dir: str

    def __post_init__(self) -> None:
        if not self.task_execution_id:
            raise ValueError("task_execution_id cannot be empty")
        if not self.work_dir:
            raise ValueError("work_dir cannot be empty")
