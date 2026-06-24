"""Default (permissive/no-op) implementations for all sub-graph extension points."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.graph_execution.ports.sub_graph_compensation import (
    CompensationDecision,
    SubGraphCompensation,
)
from shell.domain.execution.exceptions import GraphDefinitionNotFound
from shell.domain.execution.ports.sub_graph_discovery import SubGraphDiscovery
from shell.domain.execution.ports.sub_graph_governance import (
    SubGraphGovernance,
    TokenBudget,
)
from shell.domain.execution.ports.sub_graph_observer import SubGraphContext, SubGraphObserver
from shell.domain.execution.ports.sub_graph_policy import Decision, SubGraphExecutionPolicy
from shell.domain.execution.ports.sub_graph_security import Scope, SubGraphSecurity
from shell.domain.execution.ports.sub_graph_versioning import SubGraphVersioning
from shell.domain.execution.value_objects.graph_execution_definition import (
    GraphExecutionDefinition,
    GraphNodeExecutionDefinition,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
        GraphNodeExecution,
    )
    from shell.domain.execution.value_objects.execution_result import ExecutionResult


# ── Policy ───────────────────────────────────────────────────────────────────


class DefaultSubGraphExecutionPolicy(SubGraphExecutionPolicy):
    """Default policy: no retry, abort on timeout/failure, no depth limit."""

    async def on_timeout(
        self,
        graph_execution: GraphExecution,
        node: GraphNodeExecution,
    ) -> Decision:
        return Decision.abort("sub_graph_timed_out")

    async def on_failure(
        self,
        graph_execution: GraphExecution,
        node: GraphNodeExecution,
        reason: str,
    ) -> Decision:
        return Decision.abort(reason)

    async def on_depth_exceeded(
        self,
        graph_execution: GraphExecution,
        max_depth: int,
    ) -> Decision:
        return Decision.abort(f"max_depth_{max_depth}_exceeded")


# ── Observer ─────────────────────────────────────────────────────────────────


class DefaultSubGraphObserver(SubGraphObserver):
    """Default observer: no-op for all lifecycle hooks."""

    async def on_start(self, ctx: SubGraphContext) -> None:
        pass

    async def on_complete(self, ctx: SubGraphContext, result: ExecutionResult) -> None:
        pass

    async def on_fail(self, ctx: SubGraphContext, error: str) -> None:
        pass

    async def on_timeout(self, ctx: SubGraphContext) -> None:
        pass


# ── Governance ───────────────────────────────────────────────────────────────


class PermissiveSubGraphGovernance(SubGraphGovernance):
    """Default governance: everything allowed, no limits."""

    async def can_spawn(
        self,
        parent_graph_execution_id: str,
        definition_id: str,
        depth: int,
    ) -> bool:
        return True

    async def max_parallel_sub_graphs(self, graph_execution_id: str) -> int:
        return 100

    async def max_depth(self, root_graph_execution_id: str) -> int:
        return 10

    async def token_budget(self, graph_execution_id: str) -> TokenBudget | None:
        return None


# ── Compensation ─────────────────────────────────────────────────────────────


class NoOpSubGraphCompensation(SubGraphCompensation):
    """Default compensation: no rollback, continue on child failure."""

    async def compensate(
        self,
        graph_execution: GraphExecution,
        reason: str,
    ) -> None:
        pass

    async def on_child_failed(
        self,
        parent_graph: GraphExecution,
        child_graph: GraphExecution,
        tasker_node_id: str,
    ) -> CompensationDecision:
        return CompensationDecision.continue_()


# ── Security ─────────────────────────────────────────────────────────────────


class FullAccessSubGraphSecurity(SubGraphSecurity):
    """Default security: full scope, no state filtering."""

    async def resolve_scope(
        self,
        parent_graph_execution_id: str,
        sub_graph_definition_id: str,
    ) -> Scope:
        return Scope.FULL

    async def filter_state(
        self,
        parent_state: dict[str, Any],
        scope: Scope,
    ) -> dict[str, Any]:
        return dict(parent_state)


# ── Versioning ───────────────────────────────────────────────────────────────


class LatestVersionStrategy(SubGraphVersioning):
    """Uses the latest available version of the graph definition.

    Requires a callable that returns the UoW (async context manager)
    with a ``graph_definitions`` repository.
    """

    def __init__(self, unit_of_work_factory: Any) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    async def resolve_definition(
        self,
        definition_id: str,
        version: int | None,
        parent_graph_execution_id: str,
    ) -> GraphExecutionDefinition:
        from shell.domain.definition.value_objects.ids import GraphDefinitionId

        async with self._unit_of_work_factory() as unit_of_work:
            definition = await unit_of_work.graph_definitions.get_by_id(GraphDefinitionId(definition_id))
            if definition is None:
                raise ValueError(f"GraphDefinition {definition_id!r} not found")
            node_defs = [
                GraphNodeExecutionDefinition(
                    position=n.position,
                    mode=str(n.mode),
                    role=n.role,
                    node_type=n.node_type,
                    model=n.model,
                    command=n.command,
                    timeout=n.timeout,
                    retries=n.retries,
                    log_level=n.log_level,
                    max_step=n.max_step,
                    no_ask_user=n.no_ask_user,
                    autopilot=n.autopilot,
                    status_initial=n.status_initial,
                    script=n.script,
                    script_type=n.script_type,
                )
                for n in definition.graph_node_definitions
            ]
            return GraphExecutionDefinition(
                id=definition.id.value,
                name=definition.name,
                graph_node_execution_definitions=node_defs,
            )


# ── Discovery ────────────────────────────────────────────────────────────────


class DefaultSubGraphDiscovery(SubGraphDiscovery):
    """Default discovery: searches by name/purpose match.

    This is a basic fallback. Replace with VectorSubGraphDiscovery
    for semantic search via vector DB.
    """

    def __init__(self, unit_of_work_factory: Any) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    async def find_unique(self, query: str) -> str:

        query_lower = query.lower().strip()

        async with self._unit_of_work_factory() as unit_of_work:
            # Try exact name match first
            all_defs = await unit_of_work.graph_definitions.list_all()
            if all_defs is None:
                raise GraphDefinitionNotFound(query)

            best_match = None
            best_score: float = 0

            for definition in all_defs:
                name_lower = (definition.name or "").lower()
                purpose_lower = (definition.purpose or "").lower()
                score: float = 0

                if query_lower in name_lower:
                    score += 3
                if query_lower in purpose_lower:
                    score += 2

                # Check name/purpose words
                query_words = set(query_lower.split())
                name_words = set(name_lower.split())
                purpose_words = set(purpose_lower.split())

                score += len(query_words & name_words)
                score += len(query_words & purpose_words) * 0.5

                if score > best_score:
                    best_score = score
                    best_match = definition

            if best_match is None or best_score == 0:
                raise GraphDefinitionNotFound(query)

            return best_match.id.value
