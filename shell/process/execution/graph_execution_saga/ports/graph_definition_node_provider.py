from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class NodeDefinitionData:
    node_id: str
    position: int
    role: str
    mode: str
    node_type: str


class GraphDefinitionNodeProvider(Protocol):
    """Cross-BC port for the saga — provides node definitions for a graph definition.

    Implemented by an HTTP adapter in infrastructure/ that calls the definition BC API.
    """

    async def get_node_definitions(self, graph_definition_id: str) -> list[NodeDefinitionData]: ...
