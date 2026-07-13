from __future__ import annotations

from dataclasses import dataclass, field

from shell.application.definition.node_definition.dto.node_definition import (
    NodeDefinitionDto,
)


@dataclass(frozen=True, slots=True)
class GraphDefinitionDto:
    id: str
    node_definitions: list[NodeDefinitionDto] = field(default_factory=list)
