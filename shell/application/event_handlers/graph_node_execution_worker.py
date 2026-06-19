"""GraphNodeExecutionWorker — executes exactly one node step per cycle.

This handler subscribes to :class:`GraphNodeExecutionRequestedEvent` on the
in-process EventBus. Each invocation processes **exactly one** node:
runs the subprocess, records the result, and emits
:class:`GraphNodeExecutionCompletedEvent` or :class:`GraphNodeExecutionFailedEvent`.

The *next-step decision* (advance, finish, abort) is delegated to
:class:`GraphNodeExecutionResultHandler`, which subscribes to the result
events and forms the second cycle of the saga.

Cycle A (this worker)
    ``GraphNodeExecutionRequestedEvent`` → run node → record result →
    ``GraphNodeExecutionCompletedEvent`` / ``GraphNodeExecutionFailedEvent`` → return

Cycle B (GraphNodeExecutionResultHandler)
    ``GraphNodeExecutionCompletedEvent`` / ``GraphNodeExecutionFailedEvent`` →
    decide next → ``GraphNodeExecutionRequestedEvent`` / terminal event → return

Idempotency model (four-tier defence in depth)
===============================================
1. **Cursor guard** — only processes the node the workflow's ``cursor``
   actually points at. Stale events are silently dropped.
2. **Status guard** — only workflows in ``running`` are touched.
3. **Node-state guard** — only nodes whose state is still ``running``
   (not already ``done`` / ``failed``) are executed.
4. **CAS guard** — the SQL repository performs ``WHERE version = :v`` on
   save. A concurrent modification raises
   :class:`WorkflowConcurrentlyModified` which we log and swallow.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.events.events import GraphNodeExecutionRequestedEvent
from shell.domain.exceptions import WorkflowConcurrentlyModified
from shell.domain.value_objects.manifest import Manifest
from shell.domain.value_objects.mode import Mode
from shell.domain.value_objects.status import Status

if TYPE_CHECKING:
    from shell.application.ports.execution import NodeProcessRunner
    from shell.application.ports.identity import IdGenerator
    from shell.application.ports.logging import Logger
    from shell.application.ports.time import Clock
    from shell.application.ports.unit_of_work import UnitOfWork
    from shell.domain.aggregates.graph_execution import GraphExecution
    from shell.domain.entities.graph_node_execution import GraphNodeExecution
    from shell.domain.aggregates.workflow import Workflow
    from shell.domain.value_objects.execution_result import ExecutionResult
    from shell.domain.value_objects.ids import GraphNodeExecutionId


class GraphNodeExecutionWorker:
    """Cycle A: executes exactly one node per :class:`GraphNodeExecutionRequestedEvent`.

    Records the result and emits ``GraphNodeExecutionCompletedEvent`` or
    ``GraphNodeExecutionFailedEvent``.  The *next-step decision* is handled by
    :class:`GraphNodeExecutionResultHandler` (Cycle B).
    """

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        runner: NodeProcessRunner,
        logger: Logger,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._runner = runner
        self._logger = logger

    async def handle(self, event: GraphNodeExecutionRequestedEvent) -> None:
        """Handle exactly one ``GraphNodeExecutionRequestedEvent``."""

        # ── 1. Load aggregate + graph_execution ─────────────────────────────────────
        async with self._uow as uow:
            workflow = await uow.workflows.get_by_id(event.workflow_id)
            if workflow is None:
                self._logger.warning(
                    "graph_node_execution_worker.workflow_not_found",
                    workflow_id=event.workflow_id.value,
                )
                return

            task_execution = await uow.task_executions.get_current_by_id(
                workflow.task_execution_id
            )
            if task_execution is None:
                self._logger.warning(
                    "graph_node_execution_worker.task_execution_not_found",
                    task_execution_id=workflow.task_execution_id.value,
                )
                return

            graph_execution = await uow.graph_executions.get_by_task_execution_id(
                task_execution.id
            )
            work_dir = task_execution.work_dir

        if graph_execution is None:
            self._logger.error(
                "graph_node_execution_worker.graph_missing",
                workflow_id=event.workflow_id.value,
            )
            return

        if not await self._is_event_relevant(workflow, graph_execution, event):
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
        success, stdout, stderr = await self._run_node(workflow, node, event, work_dir)

        # ── 3. Reload + record result (transactional) ───────────────────
        # NOTE: next-step decision (advance / finish / abort) is handled
        # by GraphNodeExecutionResultHandler (Cycle B).
        try:
            await self._commit_step(
                event=event,
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

    async def _is_event_relevant(
        self,
        workflow: Workflow,
        graph_execution: GraphExecution,
        event: GraphNodeExecutionRequestedEvent,
    ) -> bool:
        """Four-tier idempotency: drop the event if cursor, status or node state moved on.

        For parallel execution children, the cursor guard is bypassed —
        instead we check if the node belongs to an active parallel group.
        """
        if workflow.status != Status.running():
            self._logger.debug(
                "graph_node_execution_worker.skip_terminal",
                workflow_id=workflow.id.value,
                status=workflow.status.value,
            )
            return False

        is_parallel = graph_execution.is_node_in_any_parallel_group(
            event.graph_node_execution_id.value
        )
        if not is_parallel and not workflow.cursor.points_to(event.graph_node_execution_id):
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

        # Node-state guard: skip if this node was already executed.
        state = workflow.get_graph_node_execution_state(event.graph_node_execution_id)
        if state is not None and state.status in (Status.done(), Status.failed()):
            self._logger.debug(
                "graph_node_execution_worker.skip_already_executed",
                workflow_id=workflow.id.value,
                graph_node_execution_id=event.graph_node_execution_id.value,
                node_status=state.status.value,
            )
            return False
        return True

    async def _run_node(
        self,
        workflow: Workflow,
        graph_node_execution: GraphNodeExecution,
        event: GraphNodeExecutionRequestedEvent,
        work_dir: str,
    ) -> tuple[bool, str, str]:
        manifest = self._build_manifest(graph_node_execution)
        env = self._build_env(workflow, graph_node_execution)
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
        event: GraphNodeExecutionRequestedEvent,
        success: bool,
        stdout: str,
        stderr: str,
    ) -> None:
        """Record the node execution result and stage events.

        This is Cycle A of the saga.  The *next-step decision* (advance /
        finish / abort) is handled by ``GraphNodeExecutionResultHandler``
        (Cycle B), which subscribes to the ``GraphNodeExecutionCompletedEvent``
        / ``GraphNodeExecutionFailedEvent`` events emitted here.
        """
        async with self._uow as uow:
            workflow = await uow.workflows.get_by_id(event.workflow_id)
            if workflow is None:
                return

            task_execution = await uow.task_executions.get_current_by_id(
                workflow.task_execution_id
            )
            graph_execution = (
                await uow.graph_executions.get_by_task_execution_id(task_execution.id)
                if task_execution is not None
                else None
            )

            if not await self._is_event_relevant(workflow, graph_execution, event):
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

            await uow.workflows.save(workflow)
            uow.stage_events(workflow.pull_events())

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
