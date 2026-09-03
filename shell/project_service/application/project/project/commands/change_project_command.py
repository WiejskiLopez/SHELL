from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.commands.command import Command


@dataclass(frozen=True, slots=True)
class ChangeProjectCommand(Command):
    project_id: str
    name: str | None = None
    repo_url: str | None = None

    def __post_init__(self) -> None:
        if not self.project_id:
            raise ValueError("project_id cannot be empty")
