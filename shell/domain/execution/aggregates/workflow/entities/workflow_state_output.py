from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
from shell.domain.execution.aggregates.workflow.value_objects.workflow_state_output_id import (
    WorkflowStateOutputId,
)

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class WorkflowStateOutput:
    id: WorkflowStateOutputId
    workflow_id: WorkflowId
    payload: dict[str, Any]
    created_at: datetime
