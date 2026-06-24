"""GraphNodeExecutionCompletedHandler — decides next step after a node result.

This handler subscribes to :class:`GraphNodeExecutionCompletedEvent` and
:class:`GraphNodeExecutionFailedEvent` on the in-process EventBus.  Each
invocation processes **exactly one** result and decides the next
workflow transition:

* advance to the next node (via :class:`GraphNodeExecutionNavigator`)
* fan out to parallel nodes
* evaluate conditional branches
* route to error handler on failure
* finish the workflow (terminal: ``done``)
* abort the workflow (terminal: ``failed``)

This is **Cycle B** of the node-execution saga.
Sub-graph spawning is now handled by PLANNER nodes via CrownScheduler.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.workflow.events.graph_node_execution_advanced_event import (
    GraphNodeExecutionAdvancedEvent,
)
from shell.domain.execution.aggregates.workflow.events.graph_node_execution_requested_event import (
    GraphNodeExecutionRequestedEvent,
)
from shell.domain.execution.events import (
    GraphNodeExecutionCompletedEvent,
    GraphNodeExecutionFailedEvent,
)
from shell.domain.execution.services.graph_node_execution_navigator import (
    GraphNodeExecutionNavigator,
    LinearGraphNodeExecutionNavigator,
)
from shell.domain.execution.services.graph_node_execution_policy import (
    AbortDecision,
    ContinueDecision,
    FailFastGraphNodeExecutionPolicy,
    GraphNodeExecutionPolicy,
)
from shell.domain.execution.value_objects.workflow_status import WorkflowStatus
from shell.domain.execution.value_objects.edge_type import EdgeType

if TYPE_CHECKING:
    from datetime import datetime

    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.aggregates.workflow import Workflow
    from shell.domain.execution.value_objects.ids import GraphNodeExecutionId

GraphNodeExecutionResultEvent = GraphNodeExecutionCompletedEvent | GraphNodeExecutionFailedEvent


class GraphNodeExecutionCompletedHandler:
    """Cycle B: decides next step after receiving a node execution result.

    Supports SEQUENCE, PARALLEL, CONDITIONAL, LOOP, ERROR_HANDLER, and
    DEFAULT transition types through the ``GraphNodeExecutionNavigator``.

    Sub-graph spawning is now handled by PLANNER nodes via CrownScheduler.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        logger: Logger,
        navigator: GraphNodeExecutionNavigator | None = None,
        policy: GraphNodeExecutionPolicy | None = None,

    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._logger = logger
        self._navigator: GraphNodeExecutionNavigator = (
            navigator or LinearGraphNodeExecutionNavigator()
        )
        self._policy: GraphNodeExecutionPolicy = policy or FailFastGraphNodeExecutionPolicy()

    async def handle(self, event: GraphNodeExecutionResultEvent) -> None:
        """Handle exactly one node execution result."""
        async with self._uow as uow:
            workflow = await uow.workflows.get_by_id(event.workflow_id)
            if workflow is None:
                self._logger.warning(
                    "graph_node_execution_completed_handler.workflow_not_found",
                    workflow_id=event.workflow_id.value,
                )
                return

            if workflow.status != WorkflowStatus.ACTIVE:
                logger.warning(
                    "graph_node_execution_completed_handler.skip_workflow_not_active",
                    workflow_id=event.workflow_id.value,
                    status=workflow.status.value,
                )
                return

            graph_executions = await uow.graph_executions.get_by_workflow_id(workflow.id)
            if not graph_executions:
                self._logger.warning(
                    "graph_node_execution_completed_handler.no_graph",
                    workflow_id=workflow.id.value,
                )
                return
            graph_execution = graph_executions[0]

            now = self._clock.now()

            if isinstance(event, GraphNodeExecutionCompletedEvent):
                await self._handle_completed(
                    workflow=workflow,
                    graph_execution=graph_execution,
                    graph_node_execution_id=event.graph_node_execution_id,
                    now=now,
                    uow=uow,
                )
            else:
                await self._handle_failure(
                    workflow=workflow,
                    graph_execution=graph_execution,
                    graph_node_execution_id=event.graph_node_execution_id,
                    reason=event.reason,
                    now=now,
                    uow=uow,
                )

            await uow.workflows.save(workflow)
            uow.stage_events(workflow.pull_events())

    # ── Private helpers ───────────────────────────────────────────────────

    async def _handle_completed(
        self,
        *,
        workflow: Workflow,
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
        now: datetime,
        uow: UnitOfWork,
    ) -> None:
        outgoing = graph_execution.get_outgoing_transitions(graph_node_execution_id)
        if not outgoing:
            await self._advance_or_finish(
                workflow=workflow,
                graph_execution=graph_execution,
                graph_node_execution_id=graph_node_execution_id,
                now=now,
                uow=uow,
            )
            return

        transition_types = {t.transition_type for t in outgoing}

        if EdgeType.LOOP in transition_types:
            await self._handle_loop(
                workflow=workflow,
                graph_execution=graph_execution,
                graph_node_execution_id=graph_node_execution_id,
                now=now,
                outgoing=list(outgoing),
                uow=uow,
            )
            return

        await self._advance_or_finish(
            workflow=workflow,
            graph_execution=graph_execution,
            graph_node_execution_id=graph_node_execution_id,
            now=now,
            uow=uow,
        )

    async def _handle_loop(
        self,
        *,
        workflow: Workflow,
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
        now: datetime,
        outgoing: list[Any],
        uow: UnitOfWork,
    ) -> None:
        loop_transition = None

        for t in outgoing:
            if t.transition_type == EdgeType.LOOP:
                loop_transition = t
                break

        if loop_transition is None:
            await self._advance_or_finish(
                workflow=workflow,
                graph_execution=graph_execution,
                graph_node_execution_id=graph_node_execution_id,
                now=now,
                uow=uow,
            )
            return

        counter = graph_execution.increment_loop_counter(
            transition_id=loop_transition.id.value,
            max_loop_count=loop_transition.max_loop_count or 0,
        )

        if not counter.is_exhausted:
            uow.stage_events([
                GraphNodeExecutionAdvancedEvent.now(workflow.id, graph_node_execution_id, loop_transition.target_node_execution_id, now),
                GraphNodeExecutionRequestedEvent.now(workflow.id, loop_transition.target_node_execution_id, now),
            ])
            return

        await self._advance_or_finish(
            workflow=workflow,
            graph_execution=graph_execution,
            graph_node_execution_id=graph_node_execution_id,
            now=now,
            uow=uow,
        )

    async def _advance_or_finish(
        self,
        *,
        workflow: Workflow,
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
        now: datetime,
        uow: UnitOfWork,
    ) -> None:
        next_nodes = list(
            await self._navigator.next_after_async(
                graph_execution, graph_node_execution_id, uow.graph_node_executions
            )
        )
        if not next_nodes:
            workflow.finish(now, task_execution_id=graph_execution.task_execution_id)
            return
        next_node = next_nodes[0]
        uow.stage_events([
            GraphNodeExecutionAdvancedEvent.now(workflow.id, graph_node_execution_id, next_node.id, now),
            GraphNodeExecutionRequestedEvent.now(workflow.id, next_node.id, now),
        ])

    async def _handle_failure(
        self,
        *,
        workflow: Workflow,
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
        reason: str,
        now: datetime,
        uow: UnitOfWork,
    ) -> None:
        error_handler_node = self._find_error_handler_transition(
            graph_execution, graph_node_execution_id
        )

        if error_handler_node is not None:
            uow.stage_events([
                GraphNodeExecutionAdvancedEvent.now(workflow.id, graph_node_execution_id, error_handler_node, now),
                GraphNodeExecutionRequestedEvent.now(workflow.id, error_handler_node, now),
            ])
            return

        decision = self._policy.decide_after_failure(workflow, graph_node_execution_id, reason)
        if isinstance(decision, ContinueDecision):
            await self._advance_or_finish(
                workflow=workflow,
                graph_execution=graph_execution,
                graph_node_execution_id=graph_node_execution_id,
                now=now,
                uow=uow,
            )
            return

        abort_reason = decision.reason if isinstance(decision, AbortDecision) else reason
        workflow.abort(
            reason=abort_reason,
            now=now,
            task_execution_id=graph_execution.task_execution_id,
        )

    @staticmethod
    def _find_error_handler_transition(
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
    ) -> GraphNodeExecutionId | None:
        outgoing = graph_execution.get_outgoing_transitions(graph_node_execution_id)
        for t in outgoing:
            if t.transition_type == EdgeType.ERROR_HANDLER:
                return t.target_node_execution_id
        return None

