from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.edge_execution.edge_execution import EdgeExecution
from shell.domain.execution.aggregates.edge_execution.value_objects.edge_definition_id import (
    EdgeDefinitionId,
)
from shell.domain.execution.aggregates.edge_execution.value_objects.edge_execution_id import (
    EdgeExecutionId,
)
from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.infrastructure.execution.edge_execution.persistence.sql.models.edge_execution import (
    EdgeExecutionModel,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt

