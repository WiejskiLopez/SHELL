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

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.workflow.services.compensation_handler import (
    CompensationHandler,
    NoOpCompensationHandler,
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
from shell.domain.platform.value_objects.status import Status
from shell.domain.platform.value_objects.transition_type import TransitionType

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
        compensation: CompensationHandler | None = None,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._logger = logger
        self._navigator: GraphNodeExecutionNavigator = (
            navigator or LinearGraphNodeExecutionNavigator()
        )
        self._policy: GraphNodeExecutionPolicy = policy or FailFastGraphNodeExecutionPolicy()
        self._compensation: CompensationHandler = compensation or NoOpCompensationHandler()

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

            if workflow.status != Status.running():
                self._logger.debug(
                    "graph_node_execution_completed_handler.skip_non_running",
                    workflow_id=workflow.id.value,
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

        if TransitionType.PARALLEL in transition_types:
            await self._handle_parallel(
                workflow=workflow,
                graph_execution=graph_execution,
                graph_node_execution_id=graph_node_execution_id,
                now=now,
                outgoing=list(outgoing),
                uow=uow,
            )
            return

        if TransitionType.LOOP in transition_types:
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

    async def _handle_parallel(
        self,
        *,
        workflow: Workflow,
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
        now: datetime,
        outgoing: list,
        uow: UnitOfWork,
    ) -> None:
        parallel_ids = [
            t.target_node_execution_id
            for t in outgoing
            if t.transition_type == TransitionType.PARALLEL
        ]

        if not parallel_ids:
            await self._advance_or_finish(
                workflow=workflow,
                graph_execution=graph_execution,
                graph_node_execution_id=graph_node_execution_id,
                now=now,
                uow=uow,
            )
            return

        for target_id in parallel_ids:
            workflow.request_node_execution(
                graph_node_execution_id=target_id,
                now=now,
            )

    async def _handle_loop(
        self,
        *,
        workflow: Workflow,
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
        now: datetime,
        outgoing: list,
        uow: UnitOfWork,
    ) -> None:
        loop_transition = None

        for t in outgoing:
            if t.transition_type == TransitionType.LOOP:
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

        counter = graph_execution.get_or_create_loop_counter(
            transition_id=loop_transition.id.value,
            max_loop_count=loop_transition.max_loop_count or 0,
        )
        counter.increment()

        if not counter.is_exhausted:
            workflow.advance_and_request(
                next_graph_node_execution_id=loop_transition.target_node_execution_id,
                now=now,
            )
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
        workflow.advance_and_request(next_graph_node_execution_id=next_node.id, now=now)

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
            workflow.advance_and_request(next_graph_node_execution_id=error_handler_node, now=now)
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
            compensation=self._compensation,
            task_execution_id=graph_execution.task_execution_id,
        )

    @staticmethod
    def _find_error_handler_transition(
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
    ) -> GraphNodeExecutionId | None:
        outgoing = graph_execution.get_outgoing_transitions(graph_node_execution_id)
        for t in outgoing:
            if t.transition_type == TransitionType.ERROR_HANDLER:
                return t.target_node_execution_id
        return None
