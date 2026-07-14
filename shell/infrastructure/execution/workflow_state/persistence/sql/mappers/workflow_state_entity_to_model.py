"""SQL ORM model <-> domain entity mappers for WorkflowState aggregate."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
from shell.domain.execution.aggregates.workflow_state.value_objects.workflow_state_id import (
    WorkflowStateId,
)
from shell.domain.execution.aggregates.workflow_state.workflow_state import WorkflowState
from shell.infrastructure.execution.workflow_state.persistence.sql.models.workflow_state import (
    WorkflowStateModel,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.domain.value_objects.state_direction import StateDirection
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime


def workflow_state_entity_to_model(entity: WorkflowState) -> WorkflowStateModel:
    return WorkflowStateModel(
        id=entity.id.value,
        workflow_id=entity.workflow_id.value,
        direction=entity.direction.value,
        state_data=json.dumps(json.loads(entity.state_data.value.value)),
        created_at=entity.created_at.value if entity.created_at else None,
    )