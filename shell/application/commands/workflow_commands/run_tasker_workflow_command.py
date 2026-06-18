from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RunTaskerWorkflowCommand:
    task_execution_id: str
    work_dir: str
