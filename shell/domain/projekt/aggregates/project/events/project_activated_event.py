from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.schema_version import SchemaVersion
from shell.domain.projekt.value_objects.project_id import ProjectId


@dataclass(frozen=True, slots=True)
class ProjectActivatedEvent(DomainEvent):
    project_id: ProjectId

    @classmethod
    def now(cls, project_id: ProjectId, now: CreatedAt) -> ProjectActivatedEvent:
        return cls(occurred_at=now, project_id=project_id)

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=CreatedAt.from_datetime(occurred_at),
            schema_version=SchemaVersion(schema_version),
            project_id=ProjectId(payload["project_id"]),
        )
