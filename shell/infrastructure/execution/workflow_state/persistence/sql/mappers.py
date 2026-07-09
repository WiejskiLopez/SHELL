"""SQL ORM model <-> domain entity mappers for WorkflowState aggregate."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
from shell.domain.execution.aggregates.workflow_state.value_objects.workflow_state_id import (
    WorkflowStateId,
)
from shell.domain.execution.aggregates.workflow_state.workflow_state import WorkflowState
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.state_data import StateData
from shell.domain.platform.value_objects.state_direction import StateDirection
from shell.infrastructure.execution.workflow_state.persistence.sql.models.workflow_state import (
    WorkflowStateModel,
)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def workflow_state_model_to_entity(model: WorkflowStateModel) -> WorkflowState:
    return WorkflowState.restore(
        id=WorkflowStateId(model.id),
        workflow_id=WorkflowId(model.workflow_id),
        direction=StateDirection(model.direction),
        state_data=StateData(dict(model.state_data)) if model.state_data else StateData({}),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def workflow_state_entity_to_model(entity: WorkflowState) -> WorkflowStateModel:
    return WorkflowStateModel(
        id=entity.id.value,
        workflow_id=entity.workflow_id.value,
        direction=entity.direction.value,
        state_data=entity.state_data.to_dict(),
        created_at=entity.created_at.value if entity.created_at else None,
    )
