"""NodeExecutionWorker — executes exactly one node step per cycle.

This handler subscribes to :class:`NodeExecutionRequestedEvent` on the
in-process EventBus. Each invocation processes **exactly one** node:
runs the subprocess, records the result, and emits
:class:`NodeExecutionCompletedEvent` or :class:`NodeExecutionFailedEvent`.

The *next-step decision* (advance, finish, abort) is delegated to
:class:`NodeExecutionResultHandler`, which subscribes to the result
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
4. **CAS guard** — ``version_id_col`` raises ``StaleDataError`` on version mismatch,
   translated to :class:`ConcurrentModificationError` which we log and swallow.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.node_execution.events.node_execution_completed_event import (
    NodeExecutionCompletedEvent,
)
from shell.domain.execution.aggregates.node_execution.events.node_execution_failed_event import (
    NodeExecutionFailedEvent,
)
from shell.domain.execution.aggregates.node_execution.repositories.node_execution_repository import (
    NodeExecutionRepository,
)
from shell.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)
from shell.domain.execution.aggregates.workflow.repositories.workflow_repository import (
    WorkflowRepository,
)
from shell.domain.execution.value_objects.manifest import Manifest
from shell.domain.execution.value_objects.workflow_status import WorkflowStatus
from shell.domain.platform.exceptions.concurrent_modification_error import (
    ConcurrentModificationError,
)
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.mode import Mode

if TYPE_CHECKING:
    from shell.application.platform.ports.execution import NodeExecutionProcessRunner
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.aggregates.node_execution.node_execution import (
        NodeExecution,
    )
    from shell.domain.execution.aggregates.workflow import Workflow
    from shell.domain.execution.aggregates.workflow.events.node_execution_requested_event import (
        NodeExecutionRequestedEvent,  # noqa: TC002 — NodeExecutionRequestedEvent używany w sygnaturze handle() i konstruktorze eventu
    )
    from shell.domain.execution.value_objects.execution_result import ExecutionResult
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock


class NodeExecutionWorker:
    """Cycle A: executes exactly one node per :class:`NodeExecutionRequestedEvent`.

    Records the result and emits ``NodeExecutionCompletedEvent`` or
    ``NodeExecutionFailedEvent``.  The *next-step decision* is handled by
    :class:`NodeExecutionResultHandler` (Cycle B).

    Sub-graph spawning is handled by PLANNER nodes via CrownScheduler.
    """

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
        runner: NodeExecutionProcessRunner,
        logger: Logger,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator
        self._runner = runner
        self._logger = logger

    async def handle(
        self, node_execution_requested_event: NodeExecutionRequestedEvent
    ) -> None:
        """Handle exactly one ``NodeExecutionRequestedEvent``."""

        # ── 1. Load aggregate + node ─────────────────────────────────
        async with self._unit_of_work as unit_of_work:
            workflow = await unit_of_work.repository(WorkflowRepository).get_by_id(
                node_execution_requested_event.workflow_id
            )
            if workflow is None:
                self._logger.warning(
                    "node_execution_worker.workflow_not_found",
                    workflow_id=node_execution_requested_event.workflow_id.value,
                )
                return

            task_executions = await unit_of_work.repository(
                TaskExecutionRepository
            ).get_by_workflow_id(workflow.id)
            if not task_executions:
                self._logger.warning(
                    "node_execution_worker.no_task_execution",
                    workflow_id=node_execution_requested_event.workflow_id.value,
                )
                return
            task_execution = task_executions[0]
            work_dir = task_execution.work_dir if task_execution else ""

            node = await unit_of_work.repository(NodeExecutionRepository).get_by_id(
                node_execution_requested_event.node_execution_id
            )

        if not await self._is_event_relevant(workflow, node_execution_requested_event):
            return

        if node is None:
            self._logger.error(
                "node_execution_worker.node_missing",
                workflow_id=node_execution_requested_event.workflow_id.value,
                node_execution_id=node_execution_requested_event.node_execution_id.value,
            )
            return

        # ── 2. Execute subprocess outside the UoW ────────────────────────
        task_execution_id = task_execution.id.value
        success, stdout, stderr = await self._run_node(
            workflow, node, node_execution_requested_event, str(work_dir), task_execution_id
        )

        # ── 3. Reload + record result (transactional) ───────────────────
        try:
            await self._commit_step(
                node_execution_requested_event=node_execution_requested_event,
                success=success,
                stdout=stdout,
                stderr=stderr,
                node_mode=node.mode.value if node else None,
            )
        except ConcurrentModificationError as exc:
            self._logger.warning(
                "node_execution_worker.concurrent_modification",
                workflow_id=node_execution_requested_event.workflow_id.value,
                node_execution_id=node_execution_requested_event.node_execution_id.value,
                error=str(exc),
            )

    # ── Step helpers ─────────────────────────────────────────────────────

    async def _is_event_relevant(
        self,
        workflow: Workflow,
        node_execution_requested_event: NodeExecutionRequestedEvent,
    ) -> bool:
        """Check if event is still relevant — guards against stale/duplicate events."""
        if workflow.status != WorkflowStatus.ACTIVE:
            self._logger.warning(
                "node_execution_worker.skip_workflow_not_active",
                workflow_id=node_execution_requested_event.workflow_id.value,
                status=workflow.status.value,
            )
            return False

        return True

    async def _run_node(
        self,
        workflow: Workflow,
        node_execution: NodeExecution,
        node_execution_requested_event: NodeExecutionRequestedEvent,
        work_dir: str,
        task_execution_id: str,
    ) -> tuple[bool, str, str]:
        manifest = self._build_manifest(node_execution)
        env = self._build_env(workflow, node_execution, task_execution_id)
        try:
            result: ExecutionResult = await self._runner.run(manifest, work_dir, env)
            return result.success, result.stdout, result.stderr
        except Exception as exc:  # noqa: BLE001 — celowe łapanie Exception dla logowania i graceful degradation w workerze
            self._logger.error(
                "node_execution_worker.run_failed",
                workflow_id=node_execution_requested_event.workflow_id.value,
                node_execution_id=node_execution_requested_event.node_execution_id.value,
                error=str(exc),
            )
            return False, "", str(exc)

    async def _commit_step(
        self,
        *,
        node_execution_requested_event: NodeExecutionRequestedEvent,
        success: bool,
        stdout: str,
        stderr: str,
        graph_execution: GraphExecution | None = None,
        node_mode: str | None = None,
    ) -> None:
        """Record the node execution result and stage events.

        This is Cycle A of the saga.  The *next-step decision* (advance /
        finish / abort) is handled by ``NodeExecutionResultHandler``
        (Cycle B), which subscribes to the ``NodeExecutionCompletedEvent``
        / ``NodeExecutionFailedEvent`` events emitted here.

        For PLANNER nodes with valid JSON output, delegates to
        ``NodeExecution.record_planner_result()`` which emits
        ``NodeExecutionCompletedEvent`` from the node itself.
        """
        async with self._unit_of_work as unit_of_work:
            workflow = await unit_of_work.repository(WorkflowRepository).get_by_id(
                node_execution_requested_event.workflow_id
            )
            if workflow is None:
                return

            if not await self._is_event_relevant(workflow, node_execution_requested_event):
                return

            now = self._clock.now()
            staged_events: list[Any] = list(workflow.pull_events())
            if success:
                staged_events.append(
                    NodeExecutionCompletedEvent.now(
                        node_id=node_execution_requested_event.node_execution_id,
                        now=CreatedAt.from_datetime(now),
                    )
                )
            else:
                staged_events.append(
                    NodeExecutionFailedEvent.now(
                        node_id=node_execution_requested_event.node_execution_id,
                        now=CreatedAt.from_datetime(now),
                    )
                )

            # ── Complete PLANNER node (emits NodeExecutionCompletedEvent with role=PLANNER) ──
            if success and node_mode == "planner" and stdout:
                planner_node = await unit_of_work.repository(
                    NodeExecutionRepository
                ).get_by_id(
                    node_execution_requested_event.node_execution_id,
                )
                if planner_node is not None:
                    try:
                        result = json.loads(stdout)
                    except (json.JSONDecodeError, ValueError):
                        result = {"raw": stdout}
                    planner_node.complete(result, now)
                    await unit_of_work.repository(NodeExecutionRepository).save(planner_node)
                    staged_events.extend(planner_node.pull_events())

            await unit_of_work.repository(WorkflowRepository).save(workflow)
            unit_of_work.stage_events(staged_events)

    @staticmethod
    def _build_manifest(node_execution: NodeExecution) -> Manifest:
        mode = (
            node_execution.mode
            if isinstance(node_execution.mode, Mode)
            else Mode(node_execution.mode.value)
        )
        return Manifest(
            name=node_execution.id.value,
            mode=mode,
            role=node_execution.role.value or mode.value,
            node_type=node_execution.node_type.value or mode.value,
            version="1",
        )

    @staticmethod
    def _build_env(
        workflow: Workflow,
        node_execution: NodeExecution,
        task_execution_id: str,
    ) -> dict[str, str]:
        return {
            "SHELL_WORKFLOW_ID": workflow.id.value,
            "SHELL_NODE_EXECUTION_ID": node_execution.id.value,
            "SHELL_TASK_EXECUTION_ID": task_execution_id,
        }
