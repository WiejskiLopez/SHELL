from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ImportTaskExecutionCommand:
    md_path: str
    task_execution_name: str
