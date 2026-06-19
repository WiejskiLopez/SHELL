from __future__ import annotations

from shell.domain.exceptions._base import DomainError


class WorkflowHasNoNodes(DomainError):
    """Raised when a workflow is started against a Task whose Graph is empty."""
    def __init__(self, task_execution_id: str) -> None:
        super().__init__(f"Workflow has no nodes to execute (task_execution_id={task_execution_id!r})")
