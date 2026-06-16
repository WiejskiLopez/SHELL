"""WorkflowExecutionContext — runtime context for a single workflow execution.

Captures the data that is constant across all node steps of a workflow
(working directory, correlation id) so each node-execution event stays
minimal and free from environmental concerns.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WorkflowExecutionContext:
    """Immutable VO carrying per-workflow execution context."""

    work_dir: str
    correlation_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.work_dir, str):
            raise ValueError("work_dir must be a string")
        if not isinstance(self.correlation_id, str):
            raise ValueError("correlation_id must be a string")

    @classmethod
    def empty(cls) -> WorkflowExecutionContext:
        return cls(work_dir="", correlation_id="")
