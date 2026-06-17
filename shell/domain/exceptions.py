"""Domain exceptions for shell."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain errors."""


class TaskExecutionNotFound(DomainError):
    def __init__(self, id: str) -> None:
        super().__init__(f"Task not found: {id!r}")


class WorkflowNotFound(DomainError):
    def __init__(self, workflow_id: str) -> None:
        super().__init__(f"Workflow not found: {workflow_id!r}")


class EnvelopeNotFound(DomainError):
    def __init__(self, envelope_id: str) -> None:
        super().__init__(f"Envelope not found: {envelope_id!r}")


class InvalidTaskDefinition(DomainError):
    """Raised when task markdown/yaml has invalid structure."""


class InvalidEnvelopeTransition(DomainError):
    """Raised when envelope status/stage transition is forbidden."""


class NodeNotFound(DomainError):
    def __init__(self, node_id: str) -> None:
        super().__init__(f"Node not found: {node_id!r}")


class PromptNotFound(DomainError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Prompt not found: {name!r}")


class RunnerConfigNotFound(DomainError):
    def __init__(self, package_name: str) -> None:
        super().__init__(f"RunnerConfig not found: {package_name!r}")


class RoleNotResolvable(DomainError):
    """Raised when no graph node satisfies the requested role."""


class MaxStepExceeded(DomainError):
    """Raised when envelope step >= max_step TTL."""


class InvalidNodeMode(DomainError):
    """Raised when an unknown node mode is encountered."""


class WorkflowHasNoNodes(DomainError):
    """Raised when a workflow is started against a Task whose Graph is empty."""

    def __init__(self, task_execution_id: str) -> None:
        super().__init__(f"Workflow has no nodes to execute (task_execution_id={task_execution_id!r})")


class WorkflowConcurrentlyModified(DomainError):
    """Raised when an optimistic-locking save fails (version mismatch)."""

    def __init__(self, workflow_id: str) -> None:
        super().__init__(f"Workflow was concurrently modified: id={workflow_id!r}")


class InvalidWorkflowTransition(DomainError):
    """Raised when a state-machine transition on Workflow is forbidden."""
