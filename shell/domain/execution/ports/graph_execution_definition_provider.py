from __future__ import annotations

from typing import Protocol

from shell.domain.execution.value_objects.graph_execution_definition import (
    GraphExecutionDefinition,
)


class GraphExecutionDefinitionProvider(Protocol):
    async def get_graph_definition(self, definition_id: str) -> GraphExecutionDefinition | None: ...

    async def get_graph_definition_by_name(self, name: str) -> GraphExecutionDefinition | None: ...
