from __future__ import annotations

from pydantic import BaseModel


class ProjectResponse(BaseModel):
    id: str
    name: str
    repo_url: str | None = None
    status: str
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None
