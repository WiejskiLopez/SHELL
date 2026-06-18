from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionDto:
    id: str
    position: int
    node_dir: str
    mode: str
    role: str
    node_type: str
    model: str
    command: str
