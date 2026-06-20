from __future__ import annotations

from dataclasses import dataclass, field

from shell.application.definition.dto.graph_node_definition import GraphNodeDefinitionDto


@dataclass(frozen=True, slots=True)
class GraphDefinitionDto:
    id: str
    name: str
    purpose: str
    graph_node_definitions: list[GraphNodeDefinitionDto] = field(default_factory=list)
