from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AttachGraphNodeExecutionsCommand:
    graph_execution_id: str
    graph_node_definition_executions: dict[str, str]

    @classmethod
    def validate(cls) -> None:
        pass
