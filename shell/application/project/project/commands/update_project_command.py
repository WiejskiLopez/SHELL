from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UpdateProjectCommand:
    project_id: str
    name: str | None = None
    repo_url: str | None = None

    def __post_init__(self) -> None:
        if not self.project_id:
            raise ValueError("project_id cannot be empty")
