from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.commands.command import Command


@dataclass(frozen=True, slots=True)
class ProvisionWorkspaceCommand(Command):
    """Krok sagi — dostarczany przez komendę delivery do serwisu docelowego."""

    project_id: str
    fail: bool = False

    def __post_init__(self) -> None:
        if not self.project_id:
            raise ValueError("project_id cannot be empty")
