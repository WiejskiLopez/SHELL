"""GraphNodeExecutionResultHandler — decides next step after a node result.

This handler subscribes to :class:`GraphNodeExecutionCompletedEvent` and
:class:`GraphNodeExecutionFailedEvent` on the in-process EventBus.  Each
invocation processes **exactly one** result and decides the next
workflow transition:

* advance to the next node (via :class:`NodeNavigator`)
* fan out to parallel nodes
* evaluate conditional branches
* route to error handler on failure
* finish the workflow (terminal: ``done``)
* abort the workflow (terminal: ``failed``)

This is **Cycle B** of the node-execution saga.
Sub-graph spawning is now handled by PLANNER nodes via CrownScheduler.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from shell.domain.execution.events import (
    GraphNodeExecutionCompletedEvent,
    GraphNodeExecutionFailedEvent,
    GraphNodeExecutionRequestedEvent,
    GraphNodeParallelExecutionRequestedEvent,
)
from shell.domain.execution.services.compensation_handler import (
    CompensationHandler,
    NoOpCompensationHandler,
)
from shell.domain.execution.services.graph_node_execution_navigator import (
    LinearGraphNodeExecutionNavigator,
    NodeNavigator,
)
from shell.domain.execution.services.graph_node_execution_policy import (
    AbortDecision,
    ContinueDecision,
    FailFastPolicy,
    NodeExecutionPolicy,
    RouteToErrorHandlerDecision,
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
    from shell.domain.execution.entities.graph_node_execution import GraphNodeExecution
    from shell.domain.execution.value_objects.ids import GraphNodeExecutionId

GraphNodeExecutionResultEvent = Union[GraphNodeExecutionCompletedEvent, GraphNodeExecutionFailedEvent]


class GraphNodeExecutionResultHandler:
    """Cycle B: decides next step after receiving a node execution result.

    Supports SEQUENCE, PARALLEL, CONDITIONAL, LOOP, ERROR_HANDLER, and
    DEFAULT transition types through the ``NodeNavigator``.

    Sub-graph spawning is now handled by PLANNER nodes via CrownScheduler.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        logger: Logger,
        navigator: NodeNavigator | None = None,
        policy: NodeExecutionPolicy | None = None,
        compensation: CompensationHandler | None = None,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._logger = logger
        self._navigator: NodeNavigator = navigator or LinearGraphNodeExecutionNavigator()
        self._policy: NodeExecutionPolicy = policy or FailFastPolicy()
        self._compensation: CompensationHandler = compensation or NoOpCompensationHandler()

    async def handle(self, event: GraphNodeExecutionResultEvent) -> None:
        """Handle exactly one node execution result."""
        async with self._uow as uow:
            workflow = await uow.workflows.get_by_id(event.workflow_id)
            if workflow is None:
                self._logger.warning(
                    "graph_node_execution_result_handler.workflow_not_found",
                    workflow_id=event.workflow_id.value,
                )
                return

            if workflow.status != Status.running():
                self._logger.debug(
                    "graph_node_execution_result_handler.skip_non_running",
                    workflow_id=workflow.id.value,
                    status=workflow.status.value,
                )
                return

            task_execution = await uow.task_executions.get_current_by_id(
                workflow.task_execution_id
            )
            if task_execution is None:
                self._logger.error(
                    "graph_node_execution_result_handler.task_missing",
                    workflow_id=workflow.id.value,
                )
                return

            graph_execution = await uow.graph_executions.get_by_task_execution_id(
                task_execution.id
            )
            if graph_execution is None:
                self._logger.error(
                    "graph_node_execution_result_handler.graph_missing",
                    workflow_id=workflow.id.value,
                )
                return

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
                self._handle_failure(
                    workflow=workflow,
                    graph_execution=graph_execution,
                    graph_node_execution_id=event.graph_node_execution_id,
                    reason=event.reason,
                    now=now,
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
            self._advance_or_finish(
                workflow=workflow,
                graph_execution=graph_execution,
                graph_node_execution_id=graph_node_execution_id,
                now=now,
            )
            return

        transition_types = {t.transition_type for t in outgoing}

        if TransitionType.PARALLEL in transition_types:
            self._handle_parallel(
                workflow=workflow,
                graph_execution=graph_execution,
                graph_node_execution_id=graph_node_execution_id,
                now=now,
                outgoing=list(outgoing),
            )
            return

        if TransitionType.LOOP in transition_types:
            self._handle_loop(
                workflow=workflow,
                graph_execution=graph_execution,
                graph_node_execution_id=graph_node_execution_id,
                now=now,
                outgoing=list(outgoing),
            )
            return

        self._advance_or_finish(
            workflow=workflow,
            graph_execution=graph_execution,
            graph_node_execution_id=graph_node_execution_id,
            now=now,
        )

    def _handle_parallel(
        self,
        *,
        workflow: Workflow,
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
        now: datetime,
        outgoing: list,
    ) -> None:
        parallel_nodes: list = []
        for t in outgoing:
            if t.transition_type == TransitionType.PARALLEL:
                for node in graph_execution.graph_node_executions:
                    if node.id == t.target_node_execution_id:
                        parallel_nodes.append(node)
                        break

        if not parallel_nodes:
            self._advance_or_finish(
                workflow=workflow,
                graph_execution=graph_execution,
                graph_node_execution_id=graph_node_execution_id,
                now=now,
            )
            return

        parallel_group_id = f"pg_{graph_node_execution_id.value}_{now.timestamp()}"
        target_ids = [n.id for n in parallel_nodes]
        graph_execution.create_parallel_group(
            group_id=parallel_group_id,
            fork_node_execution_id=graph_node_execution_id,
            target_node_ids=target_ids,
        )

        workflow.append_event(
            GraphNodeParallelExecutionRequestedEvent.now(
                workflow_id=workflow.id,
                fork_node_execution_id=graph_node_execution_id,
                parallel_target_node_ids=tuple(target_ids),
                parallel_group_id=parallel_group_id,
                now=now,
            )
        )

    def _handle_loop(
        self,
        *,
        workflow: Workflow,
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
        now: datetime,
        outgoing: list,
    ) -> None:
        loop_transition = None
        non_loop: list = []

        for t in outgoing:
            if t.transition_type == TransitionType.LOOP:
                loop_transition = t
            else:
                non_loop.append(t)

        if loop_transition is None:
            self._advance_or_finish(
                workflow=workflow,
                graph_execution=graph_execution,
                graph_node_execution_id=graph_node_execution_id,
                now=now,
            )
            return

        counter = graph_execution.get_or_create_loop_counter(
            transition_id=loop_transition.id.value,
            max_loop_count=loop_transition.max_loop_count or 0,
        )
        counter.increment()

        if not counter.is_exhausted:
            target_node = None
            for node in graph_execution.graph_node_executions:
                if node.id == loop_transition.target_node_execution_id:
                    target_node = node
                    break

            if target_node is not None:
                workflow.advance_and_request(
                    next_graph_node_execution_id=target_node.id, now=now
                )
                return

        self._advance_or_finish(
            workflow=workflow,
            graph_execution=graph_execution,
            graph_node_execution_id=graph_node_execution_id,
            now=now,
        )

    def _advance_or_finish(
        self,
        *,
        workflow: Workflow,
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
        now: datetime,
    ) -> None:
        next_nodes = list(
            self._navigator.next_after(graph_execution, graph_node_execution_id)
        )
        if not next_nodes:
            workflow.finish(now)
            return
        next_node = next_nodes[0]
        workflow.advance_and_request(
            next_graph_node_execution_id=next_node.id, now=now
        )

    def _handle_failure(
        self,
        *,
        workflow: Workflow,
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
        reason: str,
        now: datetime,
    ) -> None:
        error_handler_node = self._find_error_handler(
            graph_execution, graph_node_execution_id
        )

        if error_handler_node is not None:
            workflow.advance_and_request(
                next_graph_node_execution_id=error_handler_node.id, now=now
            )
            return

        decision = self._policy.decide_after_failure(workflow, graph_node_execution_id, reason)
        if isinstance(decision, ContinueDecision):
            self._advance_or_finish(
                workflow=workflow,
                graph_execution=graph_execution,
                graph_node_execution_id=graph_node_execution_id,
                now=now,
            )
            return

        abort_reason = decision.reason if isinstance(decision, AbortDecision) else reason
        workflow.abort(reason=abort_reason, now=now, compensation=self._compensation)

    @staticmethod
    def _find_error_handler(
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
    ) -> GraphNodeExecution | None:
        outgoing = graph_execution.get_outgoing_transitions(graph_node_execution_id)
        for t in outgoing:
            if t.transition_type == TransitionType.ERROR_HANDLER:
                for node in graph_execution.graph_node_executions:
                    if node.id == t.target_node_execution_id:
                        return node
        return None
