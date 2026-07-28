from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateWorkflowCommand:
    session_id: str
    project_id: str

    def __post_init__(self) -> None:
        pass
