from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetWorkflowByIdQuery:
    workflow_id: str
