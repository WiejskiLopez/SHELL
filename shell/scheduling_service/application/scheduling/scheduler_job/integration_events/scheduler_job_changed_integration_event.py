from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.events import IntegrationEvent


@dataclass(frozen=True, slots=True)
class SchedulerJobChangedIntegrationEvent(IntegrationEvent):
    scheduler_job_id: str
