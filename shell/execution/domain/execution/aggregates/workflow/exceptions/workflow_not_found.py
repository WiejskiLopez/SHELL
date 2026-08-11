from __future__ import annotations

from shell.platform.domain.exceptions.domain_error import DomainError


class WorkflowNotFound(DomainError):
    def __init__(self, workflow_id: str) -> None:
        super().__init__(f"Workflow not found: {workflow_id!r}")
