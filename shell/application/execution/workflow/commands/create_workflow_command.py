from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateWorkflowCommand:
    session_id: str | None = None

    def __post_init__(self) -> None:
        pass
