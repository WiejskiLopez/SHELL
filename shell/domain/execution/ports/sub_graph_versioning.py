"""SubGraphVersioning — resolves graph definition version at spawn time."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.definition.entities.graph_definition import GraphDefinition


class SubGraphVersioning(Protocol):
    """Wybiera wersję definicji przy spawnie sub-grafu.

    GraphDefinition → GraphExecution materialization is a snapshot.
    Once spawned, the execution is independent of definition changes.
    """

    async def resolve_definition(
        self,
        definition_id: str,
        version: int | None,
        parent_graph_execution_id: str,
    ) -> GraphDefinition:
        ...
