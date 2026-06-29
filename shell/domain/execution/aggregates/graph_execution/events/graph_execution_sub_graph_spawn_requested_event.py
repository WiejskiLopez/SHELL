from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.value_objects.graph_definition_id import GraphDefinitionIdRef
from shell.domain.platform.value_objects.state_data import StateData
from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphExecutionSubGraphSpawnRequestedEvent(DomainEvent):
    parent_graph_execution_id: GraphExecutionId
    child_graph_execution_id: GraphExecutionId
    graph_definition_id: GraphDefinitionIdRef
    state_input: StateData | None = None

    @classmethod
    def now(
        cls,
        parent_graph_execution_id: GraphExecutionId,
        child_graph_execution_id: GraphExecutionId,
        graph_definition_id: GraphDefinitionIdRef,
        now: CreatedAt,
        state_input: StateData | None = None,
    ) -> GraphExecutionSubGraphSpawnRequestedEvent:
        return cls(
            occurred_at=now,
            parent_graph_execution_id=parent_graph_execution_id,
            child_graph_execution_id=child_graph_execution_id,
            graph_definition_id=graph_definition_id,
            state_input=state_input,
        )
