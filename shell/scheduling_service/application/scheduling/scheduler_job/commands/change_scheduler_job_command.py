from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.commands.command import Command


@dataclass(frozen=True, slots=True)
class ChangeSchedulerJobCommand(Command):
    scheduler_job_id: str

    def __post_init__(self) -> None:
        if not self.scheduler_job_id:
            raise ValueError("scheduler_job_id cannot be empty")
