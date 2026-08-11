from __future__ import annotations

from shell.platform.domain.exceptions.domain_error import DomainError


class ProjectNotFound(DomainError):
    def __init__(self, project_id: str) -> None:
        super().__init__(f"Project not found: {project_id!r}")
