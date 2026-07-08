from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SchedulerDefinitionGetByIdQuery:
    scheduler_definition_id: str
