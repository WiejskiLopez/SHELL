from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from shell.domain.projekt.value_objects.project_id import ProjectId

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class ProjectStateInput:
    project_id: ProjectId
    payload: dict[str, Any]
    created_at: datetime
