"""Stan pilota sagi project_provision."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ProjectProvisionStatus(StrEnum):
    """Status cyklu życia instancji sagi."""

    RUNNING = "running"
    FAILING = "failing"
    COMPENSATED = "compensated"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class ProjectProvisionState:
    """Biznesowy stan sagi (payload zapisywany wraz z instancją)."""

    project_id: str
    status: ProjectProvisionStatus
