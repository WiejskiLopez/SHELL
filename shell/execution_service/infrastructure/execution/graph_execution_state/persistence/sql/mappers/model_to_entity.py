"""SQL ORM model <-> domain entity mapper for GraphExecutionState aggregate."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.execution_service.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.execution_service.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
    GraphExecutionState,
)
from shell.execution_service.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
    GraphExecutionStateId,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.domain.value_objects.state_direction import StateDirection
from shell.platform.infrastructure.persistence.sql.mappers._ensure_utc import (
    ensure_utc as _ensure_utc,
)
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime

if TYPE_CHECKING:
    from shell.execution_service.infrastructure.execution.graph_execution_state.persistence.sql.models.graph_execution_state import (
        GraphExecutionStateModel,
    )


def model_to_entity(model: GraphExecutionStateModel) -> GraphExecutionState:
    return GraphExecutionState.restore(
        id=GraphExecutionStateId(model.id),
        graph_execution_id=GraphExecutionId(model.graph_execution_id),
        direction=StateDirection(model.direction),
        state_data=StateData(JsonStr(json.dumps(dict(model.state_data))))
        if model.state_data
        else StateData(JsonStr("{}")),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )
