from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class CreateGraphDefinitionCommand:
    name: str
    purpose: str
    node_definitions: list[dict[str, Any]] = field(default_factory=list)
    transition_definitions: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name cannot be empty")
        if not self.purpose:
            raise ValueError("purpose cannot be empty")
