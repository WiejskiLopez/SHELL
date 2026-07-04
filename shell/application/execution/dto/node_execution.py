from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NodeExecutionDto:
    id: str
    position: int
    mode: str
    role: str
    node_type: str
    model: str | None = None
    command: str | None = None
