from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class CreateGraphDefinitionCommand:
    name: str
    purpose: str
    graph_node_definitions: list[dict[str, Any]] = field(default_factory=list)
    transition_definitions: list[dict[str, Any]] = field(default_factory=list)

    def validate(self) -> None:
        if not self.name:
            raise ValueError("name cannot be empty")
        if not self.purpose:
            raise ValueError("purpose cannot be empty")
