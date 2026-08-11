"""SQL ORM model <-> domain entity mappers for WorkflowState aggregate."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.execution.infrastructure.execution.workflow_state.persistence.sql.models.workflow_state import (
    WorkflowStateModel,
)

if TYPE_CHECKING:
    from shell.execution.domain.execution.aggregates.workflow_state.workflow_state import (
        WorkflowState,
    )


def workflow_state_entity_to_model(entity: WorkflowState) -> WorkflowStateModel:
    return WorkflowStateModel(
        id=entity.id.value,
        workflow_id=entity.workflow_id.value,
        direction=entity.direction.value,
        state_data=json.dumps(json.loads(entity.state_data.value.value)),
        created_at=entity.created_at.value if entity.created_at else None,
    )
