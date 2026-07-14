from __future__ import annotations

from typing import TYPE_CHECKING

from shell.infrastructure.execution.node_link_execution.persistence.sql.models import (
    NodeLinkExecutionModel,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.node_link_execution.node_link_execution import (
        NodeLinkExecution,
    )


def node_link_execution_entity_to_model(entity: NodeLinkExecution) -> NodeLinkExecutionModel:
    return NodeLinkExecutionModel(
        id=entity.id.value,
        graph_execution_id=entity.graph_execution_id.value,
        node_execution_id=entity.node_execution_id.value,
    )
