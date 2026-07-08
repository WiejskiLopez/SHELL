from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WorkflowStateGetByIdQuery:
    workflow_state_id: str
