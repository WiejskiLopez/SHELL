from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.edge_link_execution.edge_link_execution import (
        EdgeLinkExecution,
    )
    from shell.infrastructure.execution.edge_link_execution.persistence.sql.models.edge_link_execution import (
        EdgeLinkExecutionModel,
    )


def edge_link_execution_update_model(
    model: EdgeLinkExecutionModel,
    entity: EdgeLinkExecution,
    now: datetime,
) -> None:
    model.node_execution_id = entity.node_execution_id.value
    model.edge_execution_id = entity.edge_execution_id.value
    model.updated_at = now