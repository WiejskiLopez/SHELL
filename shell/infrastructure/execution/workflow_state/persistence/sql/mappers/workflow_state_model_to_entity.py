"""SQL ORM model <-> domain entity mappers for WorkflowState aggregate."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
from shell.domain.execution.aggregates.workflow_state.value_objects.workflow_state_id import (
    WorkflowStateId,
)
from shell.domain.execution.aggregates.workflow_state.workflow_state import WorkflowState
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.domain.value_objects.state_direction import StateDirection
from shell.platform.infrastructure.persistence.sql.mappers._ensure_utc import (
    ensure_utc as _ensure_utc,
)
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime

if TYPE_CHECKING:
    from shell.infrastructure.execution.workflow_state.persistence.sql.models.workflow_state import (
        WorkflowStateModel,
    )


def workflow_state_model_to_entity(model: WorkflowStateModel) -> WorkflowState:
    return WorkflowState.restore(
        id=WorkflowStateId(model.id),
        workflow_id=WorkflowId(model.workflow_id),
        direction=StateDirection(model.direction),
        state_data=StateData(JsonStr(json.dumps(dict(model.state_data))))
        if model.state_data
        else StateData(JsonStr("{}")),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )
