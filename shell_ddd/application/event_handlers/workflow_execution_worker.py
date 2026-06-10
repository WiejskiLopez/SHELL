"""WorkflowExecutionWorker — subscribes to WorkflowExecutionRequested and runs node subprocesses.

This is the Process Manager / Saga worker that performs the heavy, long-running
subprocess orchestration.  It is invoked by the EventBus after RunTaskerWorkflowHandler
has already persisted a RUNNING Workflow and returned control to the caller.

For HTTP API contexts where non-blocking behaviour is required, the framework layer
(e.g. FastAPI BackgroundTasks) is responsible for dispatching the event asynchronously,
not this handler.  This handler always runs its execution to completion when invoked.
"""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from shell_ddd.domain.entities.node_result import NodeResult
from shell_ddd.domain.events.events import (
    DomainEvent,
    NodeCompleted,
    NodeFailed,
    WorkflowCompleted,
    WorkflowFailed,
)
from shell_ddd.domain.value_objects.ids import NodeId, NodeResultId
from shell_ddd.domain.value_objects.manifest import Manifest
from shell_ddd.domain.value_objects.mode import Mode
from shell_ddd.domain.value_objects.status import Status

if TYPE_CHECKING:
    from shell_ddd.application.ports.ports import (
        Clock,
        EventPublisher,
        IdGenerator,
        NodeProcessRunner,
        UnitOfWork,
    )
    from shell_ddd.domain.entities.task import GraphNode
    from shell_ddd.domain.events.events import WorkflowExecutionRequested
    from shell_ddd.domain.value_objects.execution_result import ExecutionResult
    from shell_ddd.domain.value_objects.ids import WorkflowId


class WorkflowExecutionWorker:
    """Handles WorkflowExecutionRequested — orchestrates concurrent node subprocess execution.

    Execution lifecycle:
    1. Load the task graph from UoW.
    2. Run all graph nodes concurrently (Semaphore controls parallelism).
    3. Persist a NodeResult per node; update Workflow.node_states.
    4. Mark the workflow COMPLETED or FAILED.
    5. Publish NodeCompleted/NodeFailed + WorkflowCompleted/WorkflowFailed events.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        runner: NodeProcessRunner,
        event_publisher: EventPublisher,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._runner = runner
        self._event_publisher = event_publisher

    async def handle(self, event: WorkflowExecutionRequested) -> None:
        """Execute the workflow; awaits full completion before returning."""
        await self._execute(event)

    # ── Private orchestration ─────────────────────────────────────────────

    async def _execute(self, event: WorkflowExecutionRequested) -> None:
        from shell_ddd.domain.value_objects.ids import WorkflowId
        from shell_ddd.domain.value_objects.task_name import TaskName

        workflow_id = WorkflowId(event.workflow_id.value)
        semaphore = asyncio.Semaphore(event.max_parallel)

        # ── 1. Load nodes ──────────────────────────────────────────────────
        async with self._uow as uow:
            task = await uow.tasks.get_current_by_name(TaskName(event.task_name))

        nodes: list[GraphNode] = []
        if task is not None and task.graph is not None:
            nodes = list(task.graph.nodes)

        # ── 2. Execute all nodes concurrently ─────────────────────────────
        async def _run_one(node: GraphNode) -> tuple[str, bool, str, str]:
            async with semaphore:
                manifest = Manifest(
                    name=node.id.value,
                    mode=Mode(node.mode.value) if not isinstance(node.mode, Mode) else node.mode,
                    role=node.role or node.mode.value,
                    node_type=node.node_type or node.mode.value,
                    version="1",
                )
                env: dict[str, str] = {
                    "SHELL_DDD_WORKFLOW_ID": workflow_id.value,
                    "SHELL_DDD_NODE_ID": node.id.value,
                    "SHELL_DDD_TASK_NAME": event.task_name,
                }
                try:
                    result: ExecutionResult = await self._runner.run(
                        manifest, event.work_dir, env
                    )
                    return (node.id.value, result.success, result.stdout, result.stderr)
                except Exception as exc:  # noqa: BLE001
                    return (node.id.value, False, "", str(exc))

        exec_results: list[tuple[str, bool, str, str]] = list(
            await asyncio.gather(*[_run_one(n) for n in nodes])
        )

        # ── 3. Persist NodeResults + update Workflow ──────────────────────
        all_ok = all(ok for _, ok, _, _ in exec_results)
        now = self._clock.now()
        node_result_ids: dict[str, NodeResultId] = {}

        async with self._uow as uow:
            wf = await uow.workflows.get_by_id(workflow_id)
            for node_id_str, ok, stdout, stderr in exec_results:
                node_id = NodeId(node_id_str)
                node_status = Status.done() if ok else Status.failed()
                nr_id = self._id_gen.new_node_result_id()
                node_result_ids[node_id_str] = nr_id
                nr = NodeResult.new(
                    id_=nr_id,
                    node_id=node_id,
                    workflow_id=workflow_id,
                    status=node_status,
                    stdout=stdout,
                    stderr=stderr,
                    now=now,
                )
                await uow.node_results.save(nr)
                if wf is not None:
                    wf.update_node_state(node_id, node_status, now=now)

            if wf is not None:
                if all_ok:
                    wf.complete()
                else:
                    wf.fail()
                await uow.workflows.save(wf)

            domain_events: list[DomainEvent] = []
            for node_id_str, ok, _, reason in exec_results:
                node_id = NodeId(node_id_str)
                if ok:
                    domain_events.append(
                        NodeCompleted.now(node_id, workflow_id, node_result_ids[node_id_str], now=now)
                    )
                else:
                    domain_events.append(NodeFailed.now(node_id, workflow_id, reason, now=now))
            if all_ok:
                domain_events.append(WorkflowCompleted.now(workflow_id, event.task_name, now=now))
            else:
                domain_events.append(WorkflowFailed.now(workflow_id, event.task_name, now=now))
            uow.stage_events(domain_events)
            await uow.commit()

        await self._event_publisher.publish(uow.events)
