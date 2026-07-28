from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class ProjectSkillCreatedIntegrationEvent:
    event_id: str
    occurred_at: datetime
    aggregate_id: str
    aggregate_name: str
    schema_version: int
    skill_id: str
    project_id: str
