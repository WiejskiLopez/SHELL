from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ProjectDto:
    id: str
    name: str
    created_at: datetime
    repo_url: str | None = None
    status: str = "active"
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
