from __future__ import annotations

from typing import Any

from shell.application.execution.commands.attach_node_executions_command import (
    AttachNodeExecutionsCommand,
)
from shell.application.execution.commands.create_node_execution_command import (
    CreateNodeExecutionCommand,
)

_COMMAND_REGISTRY: dict[str, type] = {
    "CreateNodeExecutionCommand": CreateNodeExecutionCommand,
    "AttachNodeExecutionsCommand": AttachNodeExecutionsCommand,
}


class CommandDeserializer:
    def deserialize(self, command_type: str, payload: dict[str, Any]) -> Any | None:
        cls = _COMMAND_REGISTRY.get(command_type)
        if cls is None:
            return None
        return cls(**payload)
