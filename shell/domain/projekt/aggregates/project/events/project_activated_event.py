from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.platform.events import DomainEvent
from shell.domain.projekt.value_objects.project_id import ProjectId


@dataclass(frozen=True, slots=True)
class ProjectActivatedEvent(DomainEvent):
    project_id: ProjectId

    @classmethod
    def now(cls, project_id: ProjectId, now: datetime) -> ProjectActivatedEvent:
        return cls(occurred_at=now, project_id=project_id)

    @classmethod
    def from_payload(cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1) -> Self:
        return cls(occurred_at=occurred_at, schema_version=schema_version, project_id=ProjectId(payload.get("project_id")))
