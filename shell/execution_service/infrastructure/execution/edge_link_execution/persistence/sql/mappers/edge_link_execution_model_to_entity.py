from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution_service.domain.execution.aggregates.edge_execution.value_objects.edge_execution_id import (
    EdgeExecutionId,
)
from shell.execution_service.domain.execution.aggregates.edge_link_execution.edge_link_execution import (
    EdgeLinkExecution,
)
from shell.execution_service.domain.execution.aggregates.edge_link_execution.value_objects.edge_link_execution_id import (
    EdgeLinkExecutionId,
)
from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.platform.domain.value_objects.changed_at import ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.infrastructure.persistence.sql.mappers._ensure_utc import (
    ensure_utc as _ensure_utc,
)

if TYPE_CHECKING:
    from shell.execution_service.infrastructure.execution.edge_link_execution.persistence.sql.models.edge_link_execution import (
        EdgeLinkExecutionModel,
    )


def edge_link_execution_model_to_entity(model: EdgeLinkExecutionModel) -> EdgeLinkExecution:
    return EdgeLinkExecution.restore(
        id_=EdgeLinkExecutionId(model.id),
        node_execution_id=NodeExecutionId(model.node_execution_id),
        edge_execution_id=EdgeExecutionId(model.edge_execution_id),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
        changed_at=ChangedAt.from_datetime(_ensure_utc(model.changed_at)),
        deleted_at=DeletedAt.from_datetime(_ensure_utc(model.deleted_at)),
    )
