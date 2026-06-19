from __future__ import annotations

from shell.domain.platform.exceptions._base import DomainError


class WorkflowConcurrentlyModified(DomainError):
    """Raised when an optimistic-locking save fails (version mismatch)."""
    def __init__(self, workflow_id: str) -> None:
        super().__init__(f"Workflow was concurrently modified: id={workflow_id!r}")
