from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution.infrastructure.execution.edge_execution.persistence.sql.models.edge_execution import (
    EdgeExecutionModel,
)

if TYPE_CHECKING:
    from datetime import datetime

    from shell.execution.domain.execution.aggregates.edge_execution.edge_execution import (
        EdgeExecution,
    )


def edge_execution_entity_to_model(
    entity: EdgeExecution,
    now: datetime,
) -> EdgeExecutionModel:
    return EdgeExecutionModel(
        id=entity.id.value,
        edge_definition_id=entity.edge_definition_id.value,
        source_node_execution_id=entity.source_node_execution_id.value,
        target_node_execution_id=(
            entity.target_node_execution_id.value if entity.target_node_execution_id else None
        ),
        created_at=now,
        updated_at=now,
    )
