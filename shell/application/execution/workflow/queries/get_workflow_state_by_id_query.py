from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetWorkflowStateByIdQuery:
    workflow_state_id: str
