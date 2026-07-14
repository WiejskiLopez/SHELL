from __future__ import annotations

from typing import TYPE_CHECKING

from shell.infrastructure.execution.edge_link_execution.persistence.sql.models.edge_link_execution import (
    EdgeLinkExecutionModel,
)

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.edge_link_execution.edge_link_execution import (
        EdgeLinkExecution,
    )


def edge_link_execution_entity_to_model(
    entity: EdgeLinkExecution,
    now: datetime,
) -> EdgeLinkExecutionModel:
    return EdgeLinkExecutionModel(
        id=entity.id.value,
        node_execution_id=entity.node_execution_id.value,
        edge_execution_id=entity.edge_execution_id.value,
        created_at=now,
        updated_at=now,
    )

