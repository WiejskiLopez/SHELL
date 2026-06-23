from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.workflow.workflow_id import WorkflowId

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class WorkflowStateInput:
    id: WorkflowId
    workflow_id: WorkflowId
    payload: dict
    created_at: datetime
