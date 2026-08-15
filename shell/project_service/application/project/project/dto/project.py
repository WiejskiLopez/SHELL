from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ProjectDto:
    id: str
    name: str
    created_at: datetime
    status: str
    repo_url: str | None = None
    changed_at: datetime | None = None
    deleted_at: datetime | None = None
