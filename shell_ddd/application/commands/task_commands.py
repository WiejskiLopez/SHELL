from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ImportTaskCommand:
    md_path: str
    task_name: str
