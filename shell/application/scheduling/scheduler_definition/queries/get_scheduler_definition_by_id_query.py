from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetSchedulerDefinitionByIdQuery:
    scheduler_definition_id: str
