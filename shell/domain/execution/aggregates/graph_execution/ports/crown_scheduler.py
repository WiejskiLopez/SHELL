"""CrownScheduler — query-based parent-child sub-graph orchestration.

No state stored — all parent-child status is computed on the fly
by querying GraphExecutionRepository.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.graph_execution.ports.graph_execution_repository import (
        GraphExecutionRepository,
    )


class SubGraphChildStatus:
    """Runtime status of a sub-graph child relationship."""

    __slots__ = (
        "parent_graph_execution_id",
        "child_graph_execution_id",
        "status",
        "result",
    )

    def __init__(
        self,
        parent_graph_execution_id: GraphExecutionId,
        child_graph_execution_id: GraphExecutionId,
        status: str = "pending",
        result: dict[str, Any] | None = None,
    ) -> None:
        self.parent_graph_execution_id = parent_graph_execution_id
        self.child_graph_execution_id = child_graph_execution_id
        self.status = status
        self.result = result or {}


@dataclass(frozen=True)
class SubGraphSettledResult:
    """Result of a settled-status check — purely query-based, no derived booleans."""

    parent_graph_execution_id: GraphExecutionId
    children_statuses: tuple[SubGraphChildStatus, ...] = field(default_factory=tuple)


class CrownScheduler(Protocol):
    """Query-based parent-child sub-graph orchestrator.

    All state is computed on the fly by querying the repository.
    """

    async def compute_settled_status(
        self,
        child_graph_execution_id: GraphExecutionId,
        repo: GraphExecutionRepository,
    ) -> SubGraphSettledResult | None:
        """Compute settled status for a child graph.

        Returns None if the graph has no parent (is a root graph).
        Returns SubGraphSettledResult with all children of the parent otherwise.
        """
        ...
