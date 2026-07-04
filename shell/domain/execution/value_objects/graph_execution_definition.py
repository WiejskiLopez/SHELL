from __future__ import annotations

from dataclasses import dataclass, field

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class NodeExecutionDefinition(ValueObject):
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
    script: str
    script_type: str


@dataclass(frozen=True, slots=True)
class GraphExecutionDefinition(ValueObject):
    id: str
    name: str
    system_role: str | None = None
    node_execution_definitions: list[NodeExecutionDefinition] = field(
        default_factory=list
    )
