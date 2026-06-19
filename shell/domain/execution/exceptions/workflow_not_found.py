from __future__ import annotations

from shell.domain.platform.exceptions._base import DomainError


class WorkflowNotFound(DomainError):
    def __init__(self, workflow_id: str) -> None:
        super().__init__(f"Workflow not found: {workflow_id!r}")
