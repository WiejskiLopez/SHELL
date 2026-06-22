"""QueryBasedCrownScheduler — computes parent-child status via repository queries.

No state stored — all parent-child relationships are discovered by
querying GraphExecutionRepository on every call.
"""

from __future__ import annotations

from dataclasses import dataclass

from shell.domain.execution.aggregates.graph_execution.ports.crown_scheduler import (
    CrownScheduler,
    SubGraphChildStatus,
    SubGraphSettledResult,
)
from shell.domain.execution.aggregates.graph_execution.ports.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,
)


class QueryBasedCrownScheduler(CrownScheduler):
    """Stateless CrownScheduler — queries repo for every result."""

    async def compute_settled_status(
        self,
        child_graph_execution_id: GraphExecutionId,
        repo: GraphExecutionRepository,
    ) -> SubGraphSettledResult | None:
        child = await repo.get_by_id(child_graph_execution_id)
        if child is None or child.parent_graph_execution_id is None:
            return None

        parent_id = child.parent_graph_execution_id
        all_children = await repo.get_by_parent_id(parent_id)

        children_statuses = tuple(
            SubGraphChildStatus(
                parent_graph_execution_id=parent_id,
                child_graph_execution_id=g.id,
                status=getattr(g, "status", "unknown"),
                result=g.state_output,
            )
            for g in all_children
        )

        return SubGraphSettledResult(
            parent_graph_execution_id=parent_id,
            children_statuses=children_statuses,
        )
