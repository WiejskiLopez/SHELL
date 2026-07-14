"""SQL ORM model <-> domain entity mappers for GraphExecution aggregate."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_execution.value_objects.graph_definition_id_ref import (
    GraphDefinitionIdRef,
)
from shell.domain.execution.aggregates.graph_execution.value_objects.graph_depth import GraphDepth
from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.graph_execution.value_objects.max_subgraph_depth import (
    MaxSubgraphDepth,
)
from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.infrastructure.execution.graph_execution.persistence.sql.models.graph_execution import (
    GraphExecutionModel,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt
from shell.platform.infrastructure.context import get_correlation_id


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt

