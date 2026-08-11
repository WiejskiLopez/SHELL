from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from shell.definition.application.definition.node_definition.dto.node_definition import (
    NodeDefinitionDto,
)


@dataclass(frozen=True, slots=True)
class GraphDefinitionDto:
    id: str
    created_at: datetime
    node_definitions: list[NodeDefinitionDto] = field(default_factory=list)
