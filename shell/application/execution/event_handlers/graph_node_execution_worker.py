"""GraphNodeExecutionWorker — executes exactly one node step per cycle.

This handler subscribes to :class:`GraphNodeExecutionRequestedEvent` on the
in-process EventBus. Each invocation processes **exactly one** node:
runs the subprocess, records the result, and emits
:class:`GraphNodeExecutionCompletedEvent` or :class:`GraphNodeExecutionFailedEvent`.

The *next-step decision* (advance, finish, abort) is delegated to
:class:`GraphNodeExecutionResultHandler`, which subscribes to the result
events and forms the second cycle of the saga.

Sub-graph spawning is now handled by PLANNER nodes via CrownScheduler,
not by the Worker directly.

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

import json
from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.workflow.events.graph_node_execution_completed_event import (
    GraphNodeExecutionCompletedEvent,
)
from shell.domain.execution.aggregates.workflow.events.graph_node_execution_failed_event import (
    GraphNodeExecutionFailedEvent,
)
from shell.domain.execution.events import (
    GraphNodeExecutionRequestedEvent,  # noqa: TC002 — GraphNodeExecutionRequestedEvent używany w sygnaturze handle() i konstruktorze eventu
)
from shell.domain.execution.exceptions import WorkflowConcurrentlyModified
from shell.domain.execution.value_objects.manifest import Manifest
from shell.domain.platform.value_objects.mode import Mode
from shell.domain.execution.value_objects.workflow_status import WorkflowStatus

if TYPE_CHECKING:
    from shell.application.platform.ports.execution import GraphNodeExecutionProcessRunner
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
        GraphNodeExecution,
    )
    from shell.domain.execution.aggregates.workflow import Workflow
    from shell.domain.execution.value_objects.execution_result import ExecutionResult


class GraphNodeExecutionWorker:
    """Cycle A: executes exactly one node per :class:`GraphNodeExecutionRequestedEvent`.

    Records the result and emits ``GraphNodeExecutionCompletedEvent`` or
    ``GraphNodeExecutionFailedEvent``.  The *next-step decision* is handled by
    :class:`GraphNodeExecutionResultHandler` (Cycle B).

    Sub-graph spawning is handled by PLANNER nodes via CrownScheduler.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        runner: GraphNodeExecutionProcessRunner,
        logger: Logger,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._runner = runner
        self._logger = logger

    async def handle(self, event: GraphNodeExecutionRequestedEvent) -> None:
        """Handle exactly one ``GraphNodeExecutionRequestedEvent``."""

        # ── 1. Load aggregate + graph_execution + node ──────────────────────────────
        async with self._uow as uow:
            workflow = await uow.workflows.get_by_id(event.workflow_id)
            if workflow is None:
                self._logger.warning(
                    "graph_node_execution_worker.workflow_not_found",
                    workflow_id=event.workflow_id.value,
                )
                return

            graph_executions = await uow.graph_executions.get_by_workflow_id(workflow.id)
            if not graph_executions:
                self._logger.warning(
                    "graph_node_execution_worker.no_graph_execution",
                    workflow_id=event.workflow_id.value,
                )
                return
            graph_execution = graph_executions[0]
            task_execution = await uow.task_executions.get_current_by_id(
                graph_execution.task_execution_id
            )
            work_dir = task_execution.work_dir if task_execution else ""

            node = await uow.graph_node_executions.get_by_id(event.graph_node_execution_id)

        if not await self._is_event_relevant(workflow, event):
            return

        if node is None:
            self._logger.error(
                "graph_node_execution_worker.node_missing",
                workflow_id=event.workflow_id.value,
                graph_node_execution_id=event.graph_node_execution_id.value,
            )
            return

        # ── 2. Execute subprocess outside the UoW ────────────────────────
        task_execution_id = graph_execution.task_execution_id.value
        success, stdout, stderr = await self._run_node(
            workflow, node, event, work_dir, task_execution_id
        )

        # ── 3. Reload + record result (transactional) ───────────────────
        # NOTE: next-step decision (advance / finish / abort) is handled
        # by GraphNodeExecutionResultHandler (Cycle B).
        try:
            await self._commit_step(
                event=event,
                success=success,
                stdout=stdout,
                stderr=stderr,
                graph_execution=graph_execution,
                node_mode=node.mode.value if node else None,
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
        event: GraphNodeExecutionRequestedEvent,
    ) -> bool:
        """Check if event is still relevant — guards against stale/duplicate events."""
        if workflow.status != WorkflowStatus.ACTIVE:
            self._logger.warning(
                "graph_node_execution_worker.skip_workflow_not_active",
                workflow_id=event.workflow_id.value,
                status=workflow.status.value,
            )
            return False

        return True

    async def _run_node(
        self,
        workflow: Workflow,
        graph_node_execution: GraphNodeExecution,
        event: GraphNodeExecutionRequestedEvent,
        work_dir: str,
        task_execution_id: str,
    ) -> tuple[bool, str, str]:
        manifest = self._build_manifest(graph_node_execution)
        env = self._build_env(workflow, graph_node_execution, task_execution_id)
        try:
            result: ExecutionResult = await self._runner.run(manifest, work_dir, env)
            return result.success, result.stdout, result.stderr
        except Exception as exc:  # noqa: BLE001 — celowe łapanie Exception dla logowania i graceful degradation w workerze
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
        graph_execution: GraphExecution | None = None,
        node_mode: str | None = None,
    ) -> None:
        """Record the node execution result and stage events.

        This is Cycle A of the saga.  The *next-step decision* (advance /
        finish / abort) is handled by ``GraphNodeExecutionResultHandler``
        (Cycle B), which subscribes to the ``GraphNodeExecutionCompletedEvent``
        / ``GraphNodeExecutionFailedEvent`` events emitted here.

        For PLANNER nodes with valid JSON output, delegates to
        ``GraphNodeExecution.record_planner_result()`` which emits
        ``GraphNodeExecutionCompletedEvent`` from the node itself.
        """
        async with self._uow as uow:
            workflow = await uow.workflows.get_by_id(event.workflow_id)
            if workflow is None:
                return

            graph_executions = await uow.graph_executions.get_by_workflow_id(workflow.id)
            current_graph_execution = graph_executions[0] if graph_executions else None

            if not await self._is_event_relevant(workflow, event):
                return

            now = self._clock.now()
            staged_events: list[Any] = list(workflow.pull_events())
            if success:
                staged_events.append(
                    GraphNodeExecutionCompletedEvent.now(
                        graph_node_execution_id=event.graph_node_execution_id,
                        workflow_id=workflow.id,
                        result_id=self._id_gen.new_graph_node_execution_result_id(),
                        now=now,
                    )
                )
            else:
                staged_events.append(
                    GraphNodeExecutionFailedEvent.now(
                        graph_node_execution_id=event.graph_node_execution_id,
                        workflow_id=workflow.id,
                        reason=stderr or "unknown error",
                        now=now,
                    )
                )

            # ── Complete PLANNER node (emits GraphNodeExecutionCompletedEvent with role=PLANNER) ──
            if success and node_mode == "planner" and stdout:
                planner_node = await uow.graph_node_executions.get_by_id(
                    event.graph_node_execution_id,
                )
                if planner_node is not None:
                    try:
                        result = json.loads(stdout)
                    except (json.JSONDecodeError, ValueError):
                        result = {"raw": stdout}
                    planner_node.complete(result, now)
                    await uow.graph_node_executions.save(planner_node)
                    staged_events.extend(planner_node.pull_events())

            await uow.workflows.save(workflow)
            uow.stage_events(staged_events)

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
    def _build_env(
        workflow: Workflow,
        graph_node_execution: GraphNodeExecution,
        task_execution_id: str,
    ) -> dict[str, str]:
        return {
            "SHELL_WORKFLOW_ID": workflow.id.value,
            "SHELL_GRAPH_NODE_EXECUTION_ID": graph_node_execution.id.value,
            "SHELL_TASK_EXECUTION_ID": task_execution_id,

        }
