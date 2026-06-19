"""WorkflowExecutionContext — runtime context for a single workflow execution.

Captures the data that is constant across all node steps of a workflow
(correlation id) so each node-execution event stays minimal and free
from environmental concerns.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WorkflowExecutionContext:
    """Immutable VO carrying per-workflow execution context."""

    correlation_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.correlation_id, str):
            raise ValueError("correlation_id must be a string")

    def __str__(self) -> str:
        return f"WorkflowExecutionContext(correlation_id={self.correlation_id})"

    @classmethod
    def empty(cls) -> WorkflowExecutionContext:
        return cls(correlation_id="")
