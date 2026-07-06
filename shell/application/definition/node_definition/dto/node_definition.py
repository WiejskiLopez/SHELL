from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NodeDefinitionDto:
    id: str
    mode: str
    role: str
    node_type: str
    max_step: int | None = None
