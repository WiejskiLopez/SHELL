from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateGraphNodeExecutionCommand:
    graph_execution_id: str
    graph_node_definition_id: str
    position: int | None = None
    role: str | None = None
    mode: str | None = None
    node_type: str | None = None

    @classmethod
    def validate(cls) -> None:
        pass
