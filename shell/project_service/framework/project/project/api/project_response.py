from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ProjectResponse(BaseModel):
    id: str
    name: str
    repo_url: str | None = None
    status: str
    created_at: datetime
    changed_at: datetime | None = None
    deleted_at: datetime | None = None
