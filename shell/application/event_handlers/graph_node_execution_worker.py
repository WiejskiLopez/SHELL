"""GraphNodeExecutionWorker — Process Manager for step-by-step node execution.

The worker subscribes to :class:`GraphNodeExecutionRequested` on the in-process
EventBus. Each invocation processes **exactly one** node and then either:

* emits a fresh :class:`GraphNodeExecutionRequested` for the *next* node, or
* finishes the workflow (terminal: ``done``), or
* aborts the workflow (terminal: ``failed``) — possibly after consulting
  a configurable :class:`NodeExecutionPolicy` and invoking a
  :class:`CompensationHandler`.

This design embodies the *Process Manager / Saga* pattern: long-running
work is decomposed into a sequence of short, idempotent steps where each
step is durable, observable and re-deliverable.

Idempotency model (three-tier defence in depth)
================================================
1. **Cursor guard** — the worker only processes the node the workflow's
   ``cursor`` actually points at. Stale events are silently dropped.
2. **Status guard** — only workflows in ``running`` are touched. Terminal
   workflows ignore re-deliveries.
3. **CAS guard** — the SQL repository performs ``WHERE version = :v`` on
   save. A concurrent advance from another worker raises
   :class:`WorkflowConcurrentlyModified` which we log and swallow.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.events.events import GraphNodeExecutionRequested
from shell.domain.exceptions import WorkflowConcurrentlyModified
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
from shell.domain.value_objects.manifest import Manifest
from shell.domain.value_objects.mode import Mode
from shell.domain.value_objects.status import Status

if TYPE_CHECKING:
    from shell.application.ports.execution import NodeProcessRunner
    from shell.application.ports.identity import IdGenerator
    from shell.application.ports.logging import Logger
    from shell.application.ports.time import Clock
    from shell.application.ports.unit_of_work import UnitOfWork
    from shell.domain.entities.graph_execution import GraphExecution
    from shell.domain.entities.graph_node_execution import GraphNodeExecution
    from shell.domain.entities.workflow import Workflow
    from shell.domain.value_objects.execution_result import ExecutionResult
    from shell.domain.value_objects.ids import GraphNodeExecutionId


class GraphNodeExecutionWorker:
    """Executes one node per :class:`GraphNodeExecutionRequested` event."""

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        runner: NodeProcessRunner,
        logger: Logger,
        navigator: NodeNavigator | None = None,
        policy: NodeExecutionPolicy | None = None,
        compensation: CompensationHandler | None = None,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._runner = runner
        self._logger = logger
        self._navigator: NodeNavigator = navigator or LinearGraphNodeExecutionNavigator()
        self._policy: NodeExecutionPolicy = policy or FailFastPolicy()
        self._compensation: CompensationHandler = compensation or NoOpCompensationHandler()

    async def handle(self, event: GraphNodeExecutionRequested) -> None:
        """Handle exactly one ``GraphNodeExecutionRequested``."""

        # ── 1. Load aggregate + graph_execution ─────────────────────────────────────
        async with self._uow as uow:
            workflow = await uow.workflows.get_by_id(event.workflow_id)
            if workflow is None:
                self._logger.warning(
                    "graph_node_execution_worker.workflow_not_found",
                    workflow_id=event.workflow_id.value,
                )
                return

            if not self._is_event_relevant(workflow, event):
                return

            graph_execution = await self._load_graph_execution(uow, workflow)

        if graph_execution is None:
            self._logger.error(
                "graph_node_execution_worker.graph_missing",
                workflow_id=event.workflow_id.value,
            )
            return

        node = self._find_graph_node_execution(graph_execution, event.graph_node_execution_id)
        if node is None:
            self._logger.error(
                "graph_node_execution_worker.node_missing",
                workflow_id=event.workflow_id.value,
                graph_node_execution_id=event.graph_node_execution_id.value,
            )
            return

        # ── 2. Execute subprocess outside the UoW ────────────────────────
        success, stdout, stderr = await self._run_node(workflow, node, event)

        # ── 3. Reload + record result + decide next step (transactional) ─
        try:
            await self._commit_step(
                event=event,
                graph_execution=graph_execution,
                success=success,
                stdout=stdout,
                stderr=stderr,
            )
        except WorkflowConcurrentlyModified as exc:
            self._logger.warning(
                "graph_node_execution_worker.concurrent_modification",
                workflow_id=event.workflow_id.value,
                graph_node_execution_id=event.graph_node_execution_id.value,
                error=str(exc),
            )

    # ── Step helpers ─────────────────────────────────────────────────────

    def _is_event_relevant(self, workflow: Workflow, event: GraphNodeExecutionRequested) -> bool:
        """Three-tier idempotency: drop the event if the cursor or status moved on."""
        if workflow.status != Status.running():
            self._logger.debug(
                "graph_node_execution_worker.skip_terminal",
                workflow_id=workflow.id.value,
                status=workflow.status.value,
            )
            return False
        if not workflow.cursor.points_to(event.graph_node_execution_id):
            self._logger.debug(
                "graph_node_execution_worker.skip_stale_cursor",
                workflow_id=workflow.id.value,
                cursor=(
                    workflow.cursor.current_graph_node_execution_id.value
                    if workflow.cursor.current_graph_node_execution_id
                    else None
                ),
                requested=event.graph_node_execution_id.value,
            )
            return False
        return True

    @staticmethod
    async def _load_graph_execution(uow: UnitOfWork, workflow: Workflow) -> GraphExecution | None:

        task_execution = await uow.task_executions.get_current_by_id(workflow.task_execution_id)
        if task_execution is None:
            return None
        return await uow.graph_executions.get_by_task_execution_id(task_execution.id)

    async def _run_node(
        self,
        workflow: Workflow,
        graph_node_execution: GraphNodeExecution,
        event: GraphNodeExecutionRequested,
    ) -> tuple[bool, str, str]:
        manifest = self._build_manifest(graph_node_execution)
        env = self._build_env(workflow, graph_node_execution)
        work_dir = workflow.execution_context.work_dir
        try:
            result: ExecutionResult = await self._runner.run(manifest, work_dir, env)
            return result.success, result.stdout, result.stderr
        except Exception as exc:  # noqa: BLE001
            self._logger.error(
                "graph_node_execution_worker.run_failed",
                workflow_id=event.workflow_id.value,
                graph_node_execution_id=event.graph_node_execution_id.value,
                error=str(exc),
            )
            return False, "", str(exc)

    async def _commit_step(
        self,
        *,
        event: GraphNodeExecutionRequested,
        graph_execution: GraphExecution,
        success: bool,
        stdout: str,
        stderr: str,
    ) -> None:
        async with self._uow as uow:
            workflow = await uow.workflows.get_by_id(event.workflow_id)
            if workflow is None or not self._is_event_relevant(workflow, event):
                return

            now = self._clock.now()
            node_status = Status.done() if success else Status.failed()
            workflow.record_graph_node_execution_result(
                result_id=self._id_gen.new_graph_node_execution_result_id(),
                graph_node_execution_id=event.graph_node_execution_id,
                status=node_status,
                now=now,
                stdout=stdout,
                stderr=stderr,
                reason=stderr,
            )

            if success:
                self._advance_or_finish(
                    workflow=workflow,
                    graph_execution=graph_execution,
                    graph_node_execution_id=event.graph_node_execution_id,
                    now=now,
                )
            else:
                self._handle_failure(
                    workflow=workflow,
                    graph_execution=graph_execution,
                    graph_node_execution_id=event.graph_node_execution_id,
                    reason=stderr or "graph_node_execution failed",
                    now=now,
                )

            await uow.workflows.save(workflow)
            uow.stage_events(workflow.pull_events())
            await uow.commit()

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

    # ── Pure helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _find_graph_node_execution(
        graph_execution: GraphExecution, graph_node_execution_id: GraphNodeExecutionId
    ) -> GraphNodeExecution | None:
        for graph_node_execution in graph_execution.graph_node_executions:
            if graph_node_execution.id == graph_node_execution_id:
                return graph_node_execution
        return None

    @staticmethod
    def _build_manifest(graph_node_execution: GraphNodeExecution) -> Manifest:
        mode = (
            graph_node_execution.mode
            if isinstance(graph_node_execution.mode, Mode)
            else Mode(graph_node_execution.mode.value)
        )
        return Manifest(
            name=graph_node_execution.id.value,
            mode=mode,
            role=graph_node_execution.role or mode.value,
            node_type=graph_node_execution.node_type or mode.value,
            version="1",
        )

    @staticmethod
    def _build_env(workflow: Workflow, graph_node_execution: GraphNodeExecution) -> dict[str, str]:
        return {
            "SHELL_WORKFLOW_ID": workflow.id.value,
            "SHELL_GRAPH_NODE_EXECUTION_ID": graph_node_execution.id.value,
            "SHELL_TASK_EXECUTION_ID": workflow.task_execution_id.value,
            "SHELL_CORRELATION_ID": workflow.execution_context.correlation_id,
        }
