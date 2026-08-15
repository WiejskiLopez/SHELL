from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from shell.execution_service.domain.execution.aggregates.edge_execution.edge_execution import (
        EdgeExecution,
    )
    from shell.execution_service.infrastructure.execution.edge_execution.persistence.sql.models.edge_execution import (
        EdgeExecutionModel,
    )


def edge_execution_update_model(
    model: EdgeExecutionModel,
    entity: EdgeExecution,
    now: datetime,
) -> None:
    model.edge_definition_id = entity.edge_definition_id.value
    model.source_node_execution_id = entity.source_node_execution_id.value
    model.target_node_execution_id = (
        entity.target_node_execution_id.value if entity.target_node_execution_id else None
    )
    model.updated_at = now
