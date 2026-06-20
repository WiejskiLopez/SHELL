from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GraphNodeExecutionDefinition:
    position: int
    mode: str
    role: str
    node_type: str
    model: str
    command: str
    timeout: int
    retries: int
    log_level: str
    max_step: int | None
    no_ask_user: bool
    autopilot: bool
    status_initial: str
    extra: dict[str, Any]
    script: str
    script_type: str


@dataclass(frozen=True)
class GraphExecutionDefinition:
    id: str
    name: str
    graph_node_execution_definitions: list[GraphNodeExecutionDefinition] = field(default_factory=list)
