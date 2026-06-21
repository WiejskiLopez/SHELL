"""SubGraphObserver — lifecycle hooks for sub-graph execution."""

from __future__ import annotations

from datetime import (
    datetime,  # noqa: TC003 — datetime używany w parametrach konstruktora SubGraphContext i __slots__
)
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.value_objects.execution_result import ExecutionResult


class SubGraphContext:
    __slots__ = (
        "graph_execution_id",
        "parent_graph_execution_id",
        "depth",
        "correlation_id",
        "tags",
        "started_at",
        "duration_ms",
    )

    def __init__(
        self,
        graph_execution_id: str,
        parent_graph_execution_id: str | None = None,
        depth: int = 0,
        correlation_id: str = "",
        tags: dict | None = None,
        started_at: datetime | None = None,
        duration_ms: float | None = None,
    ) -> None:
        self.graph_execution_id = graph_execution_id
        self.parent_graph_execution_id = parent_graph_execution_id
        self.depth = depth
        self.correlation_id = correlation_id
        self.tags = tags or {}
        self.started_at = started_at
        self.duration_ms = duration_ms


class SubGraphObserver(Protocol):
    """Nasłuchuje zdarzeń cyklu życia sub-grafu."""

    async def on_start(self, ctx: SubGraphContext) -> None: ...

    async def on_complete(self, ctx: SubGraphContext, result: ExecutionResult) -> None: ...

    async def on_fail(self, ctx: SubGraphContext, error: str) -> None: ...

    async def on_timeout(self, ctx: SubGraphContext) -> None: ...
