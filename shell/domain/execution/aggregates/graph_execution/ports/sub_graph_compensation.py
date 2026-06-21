"""SubGraphCompensation — saga compensation for failed sub-graphs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution import GraphExecution


class CompensationDecision:
    __slots__ = ("action", "reason")

    def __init__(self, action: str, reason: str = "") -> None:
        self.action = action
        self.reason = reason

    @classmethod
    def abort(cls, reason: str = "") -> CompensationDecision:
        return cls("abort", reason)

    @classmethod
    def continue_(cls) -> CompensationDecision:
        return cls("continue")

    @classmethod
    def retry(cls) -> CompensationDecision:
        return cls("retry")


class SubGraphCompensation(Protocol):
    """Cofa skutki sub-grafu (Saga pattern)."""

    async def compensate(
        self,
        graph_execution: GraphExecution,
        reason: str,
    ) -> None:
        ...

    async def on_child_failed(
        self,
        parent_graph: GraphExecution,
        child_graph: GraphExecution,
        tasker_node_id: str,
    ) -> CompensationDecision:
        ...
