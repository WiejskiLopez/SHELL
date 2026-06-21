from __future__ import annotations

from dataclasses import dataclass, field

from shell.application.definition.dto.graph_node_definition import (
    GraphNodeDefinitionDto,  # noqa: TC002 — GraphNodeDefinitionDto używany w polu graph_node_definitions dataclass GraphDefinitionDto
)


@dataclass(frozen=True, slots=True)
class GraphDefinitionDto:
    id: str
    name: str
    purpose: str
    graph_node_definitions: list[GraphNodeDefinitionDto] = field(default_factory=list)
