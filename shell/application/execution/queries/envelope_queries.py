from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetEnvelopesByWorkflowQuery:
    workflow_id: str
    pending_only: bool = False
