"""SQL ORM model <-> domain entity mapper for GraphExecutionState aggregate."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
    GraphExecutionState,
)
from shell.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
    GraphExecutionStateId,
)
from shell.infrastructure.execution.graph_execution_state.persistence.sql.models.graph_execution_state import (
    GraphExecutionStateModel,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.domain.value_objects.state_direction import StateDirection
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime


def entity_to_model(entity: GraphExecutionState) -> GraphExecutionStateModel:
    return GraphExecutionStateModel(
        id=entity.id.value,
        graph_execution_id=entity.graph_execution_id.value,
        direction=entity.direction.value,
        state_data=entity.state_data,
        created_at=entity.created_at.value,
    )