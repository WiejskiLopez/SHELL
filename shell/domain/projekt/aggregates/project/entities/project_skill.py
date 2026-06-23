from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from shell.domain.projekt.value_objects.project_id import ProjectId

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class ProjectSkill:
    id: str
    project_id: ProjectId
    payload: dict[str, Any]
    created_at: datetime

    @classmethod
    def new(cls, project_id: ProjectId, payload: dict[str, Any], now: datetime) -> ProjectSkill:
        return cls(id=str(uuid.uuid4()), project_id=project_id, payload=payload, created_at=now)
