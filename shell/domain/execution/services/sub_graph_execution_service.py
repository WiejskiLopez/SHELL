"""SubGraphExecutionService — spawns child GraphExecution for sub-graph nodes.

Creates a child GraphExecution + minimal Workflow linked to the parent graph.
No child TaskExecution is created — the sub-graph shares the parent task
execution context.

All extension points are optional — if not provided, default permissive
implementations are used.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.events import GraphNodeExecutionRequestedEvent
from shell.domain.execution.ports.definition_provider import DefinitionProvider
from shell.domain.execution.value_objects.workflow_execution_context import (
    WorkflowExecutionContext,
)

if TYPE_CHECKING:
    from shell.domain.execution.entities.graph_node_execution import GraphNodeExecution
    from shell.domain.execution.value_objects.ids import GraphExecutionId
    from shell.domain.execution.ports.sub_graph_governance import SubGraphGovernance
    from shell.domain.execution.ports.sub_graph_observer import (
        SubGraphContext,
        SubGraphObserver,
    )
    from shell.domain.execution.ports.sub_graph_security import SubGraphSecurity
    from shell.domain.execution.ports.sub_graph_versioning import SubGraphVersioning
    from shell.domain.platform.ports.identity import IdGenerator
    from shell.domain.platform.ports.logging import Logger
    from shell.domain.platform.ports.time import Clock
    from shell.domain.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.services.graph_node_execution_navigator import (
        NodeNavigator,
    )


class SubGraphExecutionService:
    """Domain service: spawns a child GraphExecution for a sub-graph node.

    No child TaskExecution is created — the sub-graph reuses the parent's
    task_execution_id. A minimal Workflow is still created for the existing
    event-driven saga, but this will be simplified in future phases.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        logger: Logger,
        navigator: NodeNavigator,
        definition_provider: DefinitionProvider,
        governance: SubGraphGovernance | None = None,
        security: SubGraphSecurity | None = None,
        versioning: SubGraphVersioning | None = None,
        observer: SubGraphObserver | None = None,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._logger = logger
        self._navigator = navigator
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
        uow: UnitOfWork | None = None,
    ) -> GraphExecution:
        """Create a child GraphExecution from a graph definition.

        1. Governance: can_spawn? (depth, parallel limits)
        2. Versioning: resolve definition (pin/latest/snapshot)
        3. Security: scope + state filtering
        4. Builds child GraphExecution (no child TaskExecution)
        5. Creates minimal Workflow for event-driven execution
        6. Kicks off first node execution
        7. Observer: on_start notification
        """
        _uow = uow or self._uow
        now = self._clock.now()
        depth = parent_graph_execution.depth + 1
        parent_id = parent_graph_execution.id.value
        def_id = graph_definition_id

        # ── Governance check ──────────────────────────────────────────────
        if self._governance is not None:
            allowed = await self._governance.can_spawn(parent_id, def_id, depth)
            if not allowed:
                raise PermissionError(
                    f"Governance rejected sub-graph spawn: def={def_id}, depth={depth}"
                )

        # ── Versioning: resolve definition ────────────────────────────────
        version = parent_tasker_node.sub_graph_definition_version
        if self._versioning is not None:
            graph_definition = await self._versioning.resolve_definition(
                definition_id=def_id,
                version=version,
                parent_graph_execution_id=parent_id,
            )
        else:
            gd = await self._definition_provider.get_graph_definition(def_id)
            if gd is None:
                raise ValueError(f"GraphDefinition {def_id!r} not found")
            graph_definition = gd

        # ── Security: resolve scope + filter state ────────────────────────
        resolved_state: dict[str, Any] = dict(state_input) if state_input else {}
        if self._security is not None:
            scope = await self._security.resolve_scope(parent_id, def_id)
            resolved_state = await self._security.filter_state(resolved_state, scope)

        # ── Build child GraphExecution (no child TaskExecution) ──────────
        # ── Create Workflow for child graph ────────────────────────────
        child_workflow = Workflow.new(
            id_=self._id_gen.new_workflow_id(),
            now=now,
        )

        sub_graph_execution = GraphExecution.from_graph_definition(
            id_=self._id_gen.new_graph_execution_id(),
            task_execution_id=parent_graph_execution.task_execution_id,
            graph_definition=graph_definition,
            id_gen=self._id_gen,
            now=now,
            parent_graph_execution_id=parent_graph_execution.id,
            state_input=resolved_state,
            correlation_id=correlation_id,
            depth=depth,
            workflow_id=child_workflow.id,
        )

        first_node = self._navigator.first(sub_graph_execution)

        if first_node is not None:
            child_workflow.start_at(
                first_graph_node_execution_id=first_node.id,
                context=WorkflowExecutionContext(correlation_id=correlation_id),
                now=now,
                task_execution_id=parent_graph_execution.task_execution_id,
            )

        # ── Persist ───────────────────────────────────────────────────────
        await _uow.graph_executions.save(sub_graph_execution)
        await _uow.workflows.save(child_workflow)

        events = list(sub_graph_execution.pull_events())
        events.extend(child_workflow.pull_events())

        if first_node is not None:
            child_workflow.append_event(
                GraphNodeExecutionRequestedEvent.now(
                    workflow_id=child_workflow.id,
                    graph_node_execution_id=first_node.id,
                    now=now,
                )
            )
            events.extend(child_workflow.pull_events())

        _uow.stage_events(events)

        # ── Observer notification ─────────────────────────────────────────
        if self._observer is not None:
            ctx = SubGraphContext(
                graph_execution_id=sub_graph_execution.id.value,
                parent_graph_execution_id=parent_id,
                depth=depth,
                correlation_id=correlation_id,
                started_at=now,
            )
            await self._observer.on_start(ctx)

        self._logger.info(
            "sub_graph_execution.spawned",
            sub_graph_id=sub_graph_execution.id.value,
            parent_graph_id=parent_id,
            tasker_node_id=parent_tasker_node.id.value,
            definition_id=def_id,
            depth=depth,
        )

        return sub_graph_execution
