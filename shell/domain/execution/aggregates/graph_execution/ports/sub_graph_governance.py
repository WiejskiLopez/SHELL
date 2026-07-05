"""SubGraphGovernance — constraints and policies for sub-graph spawning."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )


class TokenBudget:
    __slots__ = ("max_tokens", "max_cost")

    def __init__(self, max_tokens: int = 0, max_cost: float = 0.0) -> None:
        self.max_tokens = max_tokens
        self.max_cost = max_cost


class SubGraphGovernance(Protocol):
    """Ograniczenia i polityki dotyczące tworzenia sub-grafów."""

    async def can_spawn(
        self,
        parent_graph_execution_id: GraphExecutionId,
        definition_id: str,
        depth: int,
    ) -> bool: ...

    async def max_parallel_sub_graphs(
        self,
        graph_execution_id: GraphExecutionId,
    ) -> int: ...

    async def max_depth(
        self,
        root_graph_execution_id: GraphExecutionId,
    ) -> int: ...

    async def token_budget(
        self,
        graph_execution_id: GraphExecutionId,
    ) -> TokenBudget | None: ...
