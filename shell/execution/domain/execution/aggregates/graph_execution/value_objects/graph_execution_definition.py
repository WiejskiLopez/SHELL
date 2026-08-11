from __future__ import annotations

from dataclasses import dataclass, field

from shell.platform.domain.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class NodeExecutionDefinition(ValueObject):
    mode: str
    role: str
    node_type: str
    max_step: int | None = None


@dataclass(frozen=True, slots=True)
class GraphExecutionDefinition(ValueObject):
    id: str
    node_execution_definitions: list[NodeExecutionDefinition] = field(default_factory=list)
