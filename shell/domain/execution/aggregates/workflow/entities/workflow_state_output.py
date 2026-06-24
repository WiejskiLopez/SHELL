from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class WorkflowStateOutput:
    id: WorkflowId
    workflow_id: WorkflowId
    payload: dict
    created_at: datetime
