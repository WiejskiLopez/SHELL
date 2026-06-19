"""GraphNodeExecutionResultHandler — decides next step after a node result.

This handler subscribes to :class:`GraphNodeExecutionCompleted` and
:class:`GraphNodeExecutionFailed` on the in-process EventBus.  Each
invocation processes **exactly one** result and decides the next
workflow transition:

* advance to the next node (via :class:`NodeNavigator`)
* finish the workflow (terminal: ``done``)
* abort the workflow (terminal: ``failed``) — possibly after consulting
  a configurable :class:`NodeExecutionPolicy` and invoking a
  :class:`CompensationHandler`.

This is **Cycle B** of the node-execution saga:

    Cycle A (GraphNodeExecutionWorker)
        ``GraphNodeExecutionRequested`` → run node → record result →
        ``GraphNodeExecutionCompleted`` / ``GraphNodeExecutionFailed`` → return

    Cycle B (this handler)
        ``GraphNodeExecutionCompleted`` / ``GraphNodeExecutionFailed`` →
        decide next → ``GraphNodeExecutionRequested`` / terminal event → return
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from shell.domain.events.events import (
    GraphNodeExecutionCompleted,
    GraphNodeExecutionFailed,
    GraphNodeExecutionRequested,
)
from shell.domain.services.compensation_handler import (
    CompensationHandler,
    NoOpCompensationHandler,
)
from shell.domain.services.graph_node_execution_navigator import (
    LinearGraphNodeExecutionNavigator,
    NodeNavigator,
)
from shell.domain.services.graph_node_execution_policy import (
    AbortDecision,
    ContinueDecision,
    FailFastPolicy,
    NodeExecutionPolicy,
)
from shell.domain.value_objects.status import Status

if TYPE_CHECKING:
    from datetime import datetime

    from shell.application.ports.identity import IdGenerator
    from shell.application.ports.logging import Logger
    from shell.application.ports.time import Clock
    from shell.application.ports.unit_of_work import UnitOfWork
    from shell.domain.aggregates.graph_execution import GraphExecution
    from shell.domain.aggregates.workflow import Workflow
    from shell.domain.value_objects.ids import GraphNodeExecutionId

GraphNodeExecutionResultEvent = Union[GraphNodeExecutionCompleted, GraphNodeExecutionFailed]


class GraphNodeExecutionResultHandler:
    """Cycle B: decides next step after receiving a node execution result.

    On ``GraphNodeExecutionCompleted``:
        Uses ``NodeNavigator.next_after()`` to find the next node.
        If found → ``advance_to()`` + emit ``GraphNodeExecutionRequested``.
        If not found → ``finish()`` (terminal: ``done``).

    On ``GraphNodeExecutionFailed``:
        Consults ``NodeExecutionPolicy.decide_after_failure()``.
        If ``ContinueDecision`` → advance (same as success path).
        If ``AbortDecision`` → ``abort()`` (terminal: ``failed``).
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

            graph_execution = await self._load_graph_execution(uow, workflow)
            if graph_execution is None:
                self._logger.error(
                    "graph_node_execution_result_handler.graph_missing",
                    workflow_id=workflow.id.value,
                )
                return

            now = self._clock.now()

            if isinstance(event, GraphNodeExecutionCompleted):
                self._advance_or_finish(
                    workflow=workflow,
                    graph_execution=graph_execution,
                    graph_node_execution_id=event.graph_node_execution_id,
                    now=now,
                )
            else:  # GraphNodeExecutionFailed
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

    async def _load_graph_execution(
        self,
        uow: UnitOfWork,
        workflow: Workflow,
    ) -> GraphExecution | None:
        task_execution = await uow.task_executions.get_current_by_id(workflow.task_execution_id)
        if task_execution is None:
            return None
        return await uow.graph_executions.get_by_task_execution_id(task_execution.id)

    def _advance_or_finish(
        self,
        *,
        workflow: Workflow,
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
        now: datetime,
    ) -> None:
        next_graph_node_executions = list(
            self._navigator.next_after(graph_execution, graph_node_execution_id)
        )
        if not next_graph_node_executions:
            workflow.finish(now)
            return
        next_graph_node_execution = next_graph_node_executions[0]
        workflow.advance_to(next_graph_node_execution_id=next_graph_node_execution.id, now=now)
        workflow.append_event(
            GraphNodeExecutionRequested.now(workflow.id, next_graph_node_execution.id, now=now)
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
