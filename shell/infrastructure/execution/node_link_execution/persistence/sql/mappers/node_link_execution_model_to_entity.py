from __future__ import annotations

from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from shell.infrastructure.execution.node_link_execution.persistence.sql.models import (
        NodeLinkExecutionModel,
    )


def node_link_execution_model_to_entity(model: NodeLinkExecutionModel) -> NodeLinkExecution:
    return NodeLinkExecution.restore(
        id=NodeLinkExecutionId(model.id),
        graph_execution_id=GraphExecutionId(model.graph_execution_id),
        node_execution_id=NodeExecutionId(model.node_execution_id),
    )

