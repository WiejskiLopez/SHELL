from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.commands.command import Command


@dataclass(frozen=True, slots=True)
class CreateNodeExecutionCommand(Command):
    graph_execution_id: str
    node_definition_id: str
    node_type: str

    def __post_init__(self) -> None:
        if not self.graph_execution_id:
            raise ValueError("graph_execution_id cannot be empty")
        if not self.node_definition_id:
            raise ValueError("node_definition_id cannot be empty")
