from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.commands.command import Command


@dataclass(frozen=True, slots=True)
class DeleteNodeExecutionCommand(Command):
    node_execution_id: str

    def __post_init__(self) -> None:
        if not self.node_execution_id:
            raise ValueError("node_execution_id cannot be empty")
