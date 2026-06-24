"""SubGraphExecutionService — spawns child GraphExecution for sub-graph nodes.

Creates a child GraphExecution linked to the parent graph.
No child TaskExecution, no child Workflow — the sub-graph shares
the parent's task execution context and is detached from workflow.

All extension points are optional — if not provided, default permissive
implementations are used.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.ports.graph_execution_definition_provider import (
    GraphExecutionDefinitionProvider,  # noqa: TC002 — GraphExecutionDefinitionProvider używany w konstruktorze SubGraphExecutionService
)
from shell.domain.execution.ports.sub_graph_observer import SubGraphContext
from shell.domain.platform.value_objects.mode import Mode

if TYPE_CHECKING:
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
        GraphNodeExecution,
    )
    from shell.domain.execution.ports.sub_graph_governance import SubGraphGovernance
    from shell.domain.execution.ports.sub_graph_observer import (
        SubGraphObserver,
    )
    from shell.domain.execution.ports.sub_graph_security import SubGraphSecurity
    from shell.domain.execution.ports.sub_graph_versioning import SubGraphVersioning
    from shell.domain.execution.value_objects.graph_execution_definition import (
        GraphExecutionDefinition,
    )
    from shell.domain.platform.ports.identity import IdGenerator


class SubGraphExecutionService:
    """Domain service: spawns a child GraphExecution for a sub-graph node.

    No child TaskExecution, no child Workflow — the sub-graph reuses the
    parent's task_execution_id and is not bound to any Workflow.
    """

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
        logger: Logger,
        definition_provider: GraphExecutionDefinitionProvider,
        governance: SubGraphGovernance | None = None,
        security: SubGraphSecurity | None = None,
        versioning: SubGraphVersioning | None = None,
        observer: SubGraphObserver | None = None,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator
        self._logger = logger
        self._definition_provider = definition_provider
        self._governance = governance
        self._security = security
        self._versioning = versioning
        self._observer = observer

    async def spawn(
        self,
        *,
        parent_graph_execution: GraphExecution,
        parent_tasker_node: GraphNodeExecution,
        graph_definition_id: str,
        state_input: dict[str, Any] | None = None,
        correlation_id: str = "",
        unit_of_work: UnitOfWork | None = None,
    ) -> GraphExecution:
        """Create a child GraphExecution from a graph definition.

        1. Governance: can_spawn? (depth, parallel limits)
        2. Versioning: resolve definition (pin/latest/snapshot)
        3. Security: scope + state filtering
        4. Builds child GraphExecution (no child TaskExecution, no child Workflow)
        5. Observer: on_start notification
        """
        _unit_of_work = unit_of_work or self._unit_of_work
        now = self._clock.now()
        depth = parent_graph_execution.depth + 1
        parent_graph_execution_id_value = parent_graph_execution.id.value

        # ── Governance check ──────────────────────────────────────────────
        if self._governance is not None:
            allowed = await self._governance.can_spawn(
                parent_graph_execution_id_value, graph_definition_id, depth
            )
            if not allowed:
                raise PermissionError(
                    f"Governance rejected sub-graph spawn: def={graph_definition_id}, depth={depth}"
                )

        # ── Versioning: resolve definition ────────────────────────────────
        version = None
        graph_definition: GraphExecutionDefinition
        if self._versioning is not None:
            graph_definition = await self._versioning.resolve_definition(
                definition_id=graph_definition_id,
                version=version,
                parent_graph_execution_id=parent_graph_execution_id_value,
            )
        else:
            gd = await self._definition_provider.get_graph_definition(graph_definition_id)
            if gd is None:
                raise ValueError(f"GraphDefinition {graph_definition_id!r} not found")
            graph_definition = gd

        # ── Security: resolve scope + filter state ────────────────────────
        resolved_state: dict[str, Any] = dict(state_input) if state_input else {}
        if self._security is not None:
            scope = await self._security.resolve_scope(
                parent_graph_execution_id_value, graph_definition_id
            )
            resolved_state = await self._security.filter_state(resolved_state, scope)

        # ── Build child GraphNodeExecutions first ──────────────────────────
        sub_graph_execution_id = self._id_generator.new_graph_execution_id()
        from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
            GraphNodeExecution as GNE,
        )

        node_ids: list[Any] = []
        for node_def in graph_definition.graph_node_execution_definitions:
            node_id = self._id_generator.new_graph_node_execution_id()
            node = GNE(
                id=node_id,
                position=node_def.position,
                mode=Mode(node_def.mode),
                role=node_def.role,
                node_type=node_def.node_type,
                model=node_def.model,
                command=node_def.command,
                timeout=node_def.timeout,
                retries=node_def.retries,
                log_level=node_def.log_level,
                max_step=node_def.max_step or 0,
                no_ask_user=node_def.no_ask_user,
                autopilot=node_def.autopilot,
                status_initial=node_def.status_initial,
                timeout_seconds=node_def.timeout,
                max_retries=node_def.retries,
                graph_execution_id=sub_graph_execution_id,
            )
            await _unit_of_work.graph_node_executions.save(node)
            node_ids.append(node_id)

        # ── Build child GraphExecution (no child TaskExecution, no child Workflow) ──
        sub_graph_execution = GraphExecution.from_graph_definition(
            id_=sub_graph_execution_id,
            task_execution_id=parent_graph_execution.task_execution_id,
            graph_definition=graph_definition,
            node_ids=node_ids,
            id_generator=self._id_generator,
            now=now,
            parent_graph_execution_id=parent_graph_execution.id,
            state_input=resolved_state,
            correlation_id=correlation_id,
            depth=depth,
        )

        # ── Persist ───────────────────────────────────────────────────────
        await _unit_of_work.graph_executions.save(sub_graph_execution)

        _unit_of_work.stage_events(list(sub_graph_execution.pull_events()))

        # ── Observer notification ─────────────────────────────────────────
        if self._observer is not None:
            sub_graph_context = SubGraphContext(
                graph_execution_id=sub_graph_execution.id.value,
                parent_graph_execution_id=parent_graph_execution_id_value,
                depth=depth,
                correlation_id=correlation_id,
                started_at=now,
            )
            await self._observer.on_start(sub_graph_context)

        self._logger.info(
            "sub_graph_execution.spawned",
            sub_graph_id=sub_graph_execution.id.value,
            parent_graph_id=parent_graph_execution_id_value,
            tasker_node_id=parent_tasker_node.id.value,
            definition_id=graph_definition_id,
            depth=depth,
        )

        return sub_graph_execution
