from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.definition.node_definition.dto.node_definition import (
        NodeDefinitionDto,  # noqa: TC002 — NodeDefinitionDto używany w polu node_definitions dataclass GraphDefinitionDto
    )


@dataclass(frozen=True, slots=True)
class GraphDefinitionDto:
    id: str
    node_definitions: list[NodeDefinitionDto] = field(default_factory=list)
