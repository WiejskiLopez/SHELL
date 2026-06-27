from __future__ import annotations

from typing import Any

from shell.application.execution.commands.attach_graph_node_executions_command import (
    AttachGraphNodeExecutionsCommand,
)
from shell.application.execution.commands.create_graph_node_execution_command import (
    CreateGraphNodeExecutionCommand,
)

_COMMAND_REGISTRY: dict[str, type] = {
    "CreateGraphNodeExecutionCommand": CreateGraphNodeExecutionCommand,
    "AttachGraphNodeExecutionsCommand": AttachGraphNodeExecutionsCommand,
}


class CommandDeserializer:
    def deserialize(self, command_type: str, payload: dict[str, Any]) -> Any | None:
        cls = _COMMAND_REGISTRY.get(command_type)
        if cls is None:
            return None
        return cls(**payload)
