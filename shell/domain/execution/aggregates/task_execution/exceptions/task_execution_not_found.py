from __future__ import annotations

from shell.domain.platform.exceptions.domain_error import DomainError


class TaskExecutionNotFound(DomainError):
    def __init__(self, id: str) -> None:
        super().__init__(f"Task not found: {id!r}")
