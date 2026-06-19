"""SubGraphExecutionPolicy — decisions about sub-graph lifecycle."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.entities.graph_node_execution import GraphNodeExecution


class Decision:
    """Open extension point for policy decisions."""
    __slots__ = ("action", "payload")

    def __init__(self, action: str, payload: dict | None = None) -> None:
        self.action = action
        self.payload = payload or {}

    @classmethod
    def retry(cls, delay_seconds: int = 0) -> Decision:
        return cls("retry", {"delay_seconds": delay_seconds})

    @classmethod
    def abort(cls, reason: str = "") -> Decision:
        return cls("abort", {"reason": reason})

    @classmethod
    def compensate(cls, reason: str = "") -> Decision:
        return cls("compensate", {"reason": reason})

    @classmethod
    def skip(cls) -> Decision:
        return cls("skip")

    @classmethod
    def fallback(cls) -> Decision:
        return cls("fallback")


class SubGraphExecutionPolicy(Protocol):
    """Polityka wykonania sub-grafu — timeout, retry, failure handling."""

    async def on_timeout(
        self,
        graph_execution: GraphExecution,
        node: GraphNodeExecution,
    ) -> Decision:
        ...

    async def on_failure(
        self,
        graph_execution: GraphExecution,
        node: GraphNodeExecution,
        reason: str,
    ) -> Decision:
        ...

    async def on_depth_exceeded(
        self,
        graph_execution: GraphExecution,
        max_depth: int,
    ) -> Decision:
        ...
