from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.edge_execution.value_objects.edge_execution_id import (
    EdgeExecutionId,
)
from shell.domain.execution.aggregates.edge_link_execution.edge_link_execution import (
    EdgeLinkExecution,
)
from shell.domain.execution.aggregates.edge_link_execution.value_objects.edge_link_execution_id import (
    EdgeLinkExecutionId,
)
from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.infrastructure.execution.edge_link_execution.persistence.sql.models.edge_link_execution import (
    EdgeLinkExecutionModel,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt


def edge_link_execution_update_model(
    model: EdgeLinkExecutionModel,
    entity: EdgeLinkExecution,
    now: datetime,
) -> None:
    model.node_execution_id = entity.node_execution_id.value
    model.edge_execution_id = entity.edge_execution_id.value
    model.updated_at = now