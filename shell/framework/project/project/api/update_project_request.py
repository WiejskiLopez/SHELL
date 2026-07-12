from __future__ import annotations

from pydantic import BaseModel, Field


class UpdateProjectRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=500)
    repo_url: str | None = None
