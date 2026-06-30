from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ImportTaskExecutionCommand:
    md_path: str
    task_execution_name: str

    def __post_init__(self) -> None:
        if not self.md_path:
            raise ValueError("md_path cannot be empty")
        if not self.task_execution_name:
            raise ValueError("task_execution_name cannot be empty")
