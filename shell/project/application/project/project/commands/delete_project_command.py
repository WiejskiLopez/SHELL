from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeleteProjectCommand:
    project_id: str

    def __post_init__(self) -> None:
        if not self.project_id:
            raise ValueError("project_id cannot be empty")
