from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeleteWorkflowCommand:
    workflow_id: str

    def __post_init__(self) -> None:
        if not self.workflow_id:
            raise ValueError("workflow_id cannot be empty")
