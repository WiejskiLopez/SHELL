from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
from shell.domain.execution.aggregates.workflow.value_objects.workflow_state_input_id import (
    WorkflowStateInputId,
)

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class WorkflowStateInput:
    id: WorkflowStateInputId
    workflow_id: WorkflowId
    payload: dict[str, Any]
    created_at: datetime
