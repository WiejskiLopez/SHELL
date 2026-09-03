from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.commands.command import Command


@dataclass(frozen=True, slots=True)
class ChangeIngestionCommand(Command):
    ingestion_id: str

    def __post_init__(self) -> None:
        if not self.ingestion_id:
            raise ValueError("ingestion_id cannot be empty")
