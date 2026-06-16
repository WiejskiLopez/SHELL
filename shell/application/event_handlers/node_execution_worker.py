"""NodeExecutionWorker — Process Manager for step-by-step node execution.

The worker subscribes to :class:`NodeExecutionRequested` on the in-process
EventBus. Each invocation processes **exactly one** node and then either:

* emits a fresh :class:`NodeExecutionRequested` for the *next* node, or
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

from shell.domain.events.events import NodeExecutionRequested
from shell.domain.exceptions import WorkflowConcurrentlyModified
from shell.domain.services.compensation_handler import (
    CompensationHandler,
    NoOpCompensationHandler,
)
from shell.domain.services.node_execution_policy import (
    AbortDecision,
    ContinueDecision,
    FailFastPolicy,
    NodeExecutionPolicy,
)
from shell.domain.services.node_navigator import (
    LinearNodeNavigator,
    NodeNavigator,
)
from shell.domain.value_objects.manifest import Manifest
from shell.domain.value_objects.mode import Mode
from shell.domain.value_objects.status import Status

if TYPE_CHECKING:
    from datetime import datetime

    from shell.application.ports.execution import NodeProcessRunner
    from shell.application.ports.identity import IdGenerator
    from shell.application.ports.logging import Logger
    from shell.application.ports.time import Clock
    from shell.application.ports.unit_of_work import UnitOfWork
    from shell.domain.entities.graph import Graph
    from shell.domain.entities.graph_node import GraphNode
    from shell.domain.entities.workflow import Workflow
    from shell.domain.value_objects.execution_result import ExecutionResult
    from shell.domain.value_objects.ids import NodeId


class NodeExecutionWorker:
    """Executes one node per :class:`NodeExecutionRequested` event."""

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
        self._navigator: NodeNavigator = navigator or LinearNodeNavigator()
        self._policy: NodeExecutionPolicy = policy or FailFastPolicy()
        self._compensation: CompensationHandler = (
            compensation or NoOpCompensationHandler()
        )

    async def handle(self, event: NodeExecutionRequested) -> None:
        """Handle exactly one ``NodeExecutionRequested``."""

        # ── 1. Load aggregate + graph ─────────────────────────────────────
        async with self._uow as uow:
            workflow = await uow.workflows.get_by_id(event.workflow_id)
            if workflow is None:
                self._logger.warning(
                    "node_execution_worker.workflow_not_found",
                    workflow_id=event.workflow_id.value,
                )
                return

            if not self._is_event_relevant(workflow, event):
                return

            graph = await self._load_graph(uow, workflow)

        if graph is None:
            self._logger.error(
                "node_execution_worker.graph_missing",
                workflow_id=event.workflow_id.value,
            )
            return

        node = self._find_node(graph, event.node_id)
        if node is None:
            self._logger.error(
                "node_execution_worker.node_missing",
                workflow_id=event.workflow_id.value,
                node_id=event.node_id.value,
            )
            return

        # ── 2. Execute subprocess outside the UoW ────────────────────────
        success, stdout, stderr = await self._run_node(workflow, node, event)

        # ── 3. Reload + record result + decide next step (transactional) ─
        try:
            await self._commit_step(
                event=event,
                graph=graph,
                success=success,
                stdout=stdout,
                stderr=stderr,
            )
        except WorkflowConcurrentlyModified as exc:
            self._logger.warning(
                "node_execution_worker.concurrent_modification",
                workflow_id=event.workflow_id.value,
                node_id=event.node_id.value,
                error=str(exc),
            )

    # ── Step helpers ─────────────────────────────────────────────────────

    def _is_event_relevant(
        self, workflow: Workflow, event: NodeExecutionRequested
    ) -> bool:
        """Three-tier idempotency: drop the event if the cursor or status moved on."""
        if workflow.status != Status.running():
            self._logger.debug(
                "node_execution_worker.skip_terminal",
                workflow_id=workflow.id.value,
                status=workflow.status.value,
            )
            return False
        if not workflow.cursor.points_to(event.node_id):
            self._logger.debug(
                "node_execution_worker.skip_stale_cursor",
                workflow_id=workflow.id.value,
                cursor=(
                    workflow.cursor.current_node_id.value
                    if workflow.cursor.current_node_id
                    else None
                ),
                requested=event.node_id.value,
            )
            return False
        return True

    @staticmethod
    async def _load_graph(uow: UnitOfWork, workflow: Workflow) -> Graph | None:

        task = await uow.tasks.get_current_by_id(workflow.task_id)
        if task is None:
            return None
        return await uow.graphs.get_by_task_id(task.id)

    async def _run_node(
        self,
        workflow: Workflow,
        node: GraphNode,
        event: NodeExecutionRequested,
    ) -> tuple[bool, str, str]:
        manifest = self._build_manifest(node)
        env = self._build_env(workflow, node)
        work_dir = workflow.execution_context.work_dir
        try:
            result: ExecutionResult = await self._runner.run(manifest, work_dir, env)
            return result.success, result.stdout, result.stderr
        except Exception as exc:  # noqa: BLE001
            self._logger.error(
                "node_execution_worker.run_failed",
                workflow_id=event.workflow_id.value,
                node_id=event.node_id.value,
                error=str(exc),
            )
            return False, "", str(exc)

    async def _commit_step(
        self,
        *,
        event: NodeExecutionRequested,
        graph: Graph,
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
            workflow.record_node_result(
                result_id=self._id_gen.new_node_result_id(),
                node_id=event.node_id,
                status=node_status,
                now=now,
                stdout=stdout,
                stderr=stderr,
                reason=stderr,
            )

            if success:
                self._advance_or_finish(workflow=workflow, graph=graph, node_id=event.node_id, now=now)
            else:
                self._handle_failure(
                    workflow=workflow,
                    graph=graph,
                    node_id=event.node_id,
                    reason=stderr or "node failed",
                    now=now,
                )

            await uow.workflows.save(workflow)
            uow.stage_events(workflow.pull_events())
            await uow.commit()

    def _advance_or_finish(
        self,
        *,
        workflow: Workflow,
        graph: Graph,
        node_id: NodeId,
        now: datetime,
    ) -> None:
        next_nodes = list(self._navigator.next_after(graph, node_id))
        if not next_nodes:
            workflow.finish(now)
            return
        next_node = next_nodes[0]
        workflow.advance_to(next_node_id=next_node.id, now=now)
        workflow.append_event(
            NodeExecutionRequested.now(workflow.id, next_node.id, now=now)
        )

    def _handle_failure(
        self,
        *,
        workflow: Workflow,
        graph: Graph,
        node_id: NodeId,
        reason: str,
        now: datetime,
    ) -> None:
        decision = self._policy.decide_after_failure(workflow, node_id, reason)
        if isinstance(decision, ContinueDecision):
            self._advance_or_finish(workflow=workflow, graph=graph, node_id=node_id, now=now)
            return

        abort_reason = decision.reason if isinstance(decision, AbortDecision) else reason
        workflow.abort(reason=abort_reason, now=now, compensation=self._compensation)

    # ── Pure helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _find_node(graph: Graph, node_id: NodeId) -> GraphNode | None:
        for n in graph.nodes:
            if n.id == node_id:
                return n
        return None

    @staticmethod
    def _build_manifest(node: GraphNode) -> Manifest:
        mode = node.mode if isinstance(node.mode, Mode) else Mode(node.mode.value)
        return Manifest(
            name=node.id.value,
            mode=mode,
            role=node.role or mode.value,
            node_type=node.node_type or mode.value,
            version="1",
        )

    @staticmethod
    def _build_env(workflow: Workflow, node: GraphNode) -> dict[str, str]:
        return {
            "SHELL_WORKFLOW_ID": workflow.id.value,
            "SHELL_NODE_ID": node.id.value,
            "SHELL_TASK_ID": workflow.task_id,
            "SHELL_CORRELATION_ID": workflow.execution_context.correlation_id,
        }
