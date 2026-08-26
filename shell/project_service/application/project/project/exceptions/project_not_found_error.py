from __future__ import annotations

from shell.platform.domain.exceptions import DomainError


class ProjectNotFoundError(DomainError):
    def __init__(self, project_id: str) -> None:
        super().__init__(f"Project not found: {project_id}")
