from __future__ import annotations

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.domain.execution.aggregates.node_link_execution.node_link_execution import (
    NodeLinkExecution,
)
from shell.domain.execution.aggregates.node_link_execution.value_objects.node_link_execution_id import (
    NodeLinkExecutionId,
)
from shell.infrastructure.execution.node_link_execution.persistence.sql.models import (
    NodeLinkExecutionModel,
)


def node_link_execution_entity_to_model(entity: NodeLinkExecution) -> NodeLinkExecutionModel:
    return NodeLinkExecutionModel(
        id=entity.id.value,
        graph_execution_id=entity.graph_execution_id.value,
        node_execution_id=entity.node_execution_id.value,
    )