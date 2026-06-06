"""RunTaskerWorkflowHandler — orchestrates concurrent execution of all graph nodes."""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from shell_ddd.domain.entities.node_result import NodeResult
from shell_ddd.domain.entities.workflow import Workflow
from shell_ddd.domain.events.events import (
    DomainEvent,
    NodeCompleted,
    NodeFailed,
    WorkflowCompleted,
    WorkflowFailed,
    WorkflowStarted,
)
from shell_ddd.domain.exceptions import TaskNotFound
from shell_ddd.domain.value_objects.ids import NodeId, NodeResultId
from shell_ddd.domain.value_objects.manifest import Manifest
from shell_ddd.domain.value_objects.mode import Mode
from shell_ddd.domain.value_objects.status import Status
from shell_ddd.domain.value_objects.task_name import TaskName

if TYPE_CHECKING:
    from shell_ddd.application.commands.commands import RunTaskerWorkflowCommand
    from shell_ddd.application.ports.ports import (
        Clock,
        EventPublisher,
        IdGenerator,
        NodeProcessRunner,
        UnitOfWork,
    )
    from shell_ddd.domain.entities.task import GraphNode
    from shell_ddd.domain.value_objects.execution_result import ExecutionResult


class RunTaskerWorkflowHandler:
    """Executes all nodes of a task graph concurrently and persists their results.

    Workflow lifecycle:
    1. Load task + graph from UoW.
    2. Create a new Workflow, mark it ``running``.
    3. Run all non-router nodes concurrently (Semaphore controls parallelism).
    4. Persist NodeResult per node, update Workflow.node_states.
    5. Mark workflow COMPLETED (all done) or FAILED (any failed).
    6. Publish NodeCompleted/NodeFailed + WorkflowCompleted/WorkflowFailed.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        runner: NodeProcessRunner,
        events: EventPublisher,
        max_parallel: int = 4,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._runner = runner
        self._events = events
        self._max_parallel = max_parallel

    async def handle(self, cmd: RunTaskerWorkflowCommand) -> str:
        """Run all task graph nodes concurrently; return the workflow id."""
        task_name = TaskName(cmd.task_name)
        effective_parallel = cmd.max_parallel or self._max_parallel

        # ── 1. Load task ──────────────────────────────────────────────────
        async with self._uow as uow:
            task = await uow.tasks.get_current_by_name(task_name)
            if task is None:
                raise TaskNotFound(cmd.task_name)
            nodes: list[GraphNode] = list(task.graph.nodes) if task.graph else []

            # ── 2. Create Workflow ─────────────────────────────────────────
            workflow = Workflow.new(
                id_=self._id_gen.new_workflow_id(),
                task_name=cmd.task_name,
                now=self._clock.now(),
            )
            workflow.start()
            await uow.workflows.save(workflow)
            await uow.commit()

        workflow_id = workflow.id
        await self._events.publish([WorkflowStarted.now(workflow_id, cmd.task_name)])

        # ── 3. Execute all nodes concurrently ─────────────────────────────
        semaphore = asyncio.Semaphore(effective_parallel)

        async def _run_one(node: GraphNode) -> tuple[str, bool, str, str]:
            """Run a single node; return (node_id_str, success, stdout, stderr)."""
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
                    "SHELL_DDD_TASK_NAME": cmd.task_name,
                }
                try:
                    result: ExecutionResult = await self._runner.run(
                        manifest, cmd.work_dir, env
                    )
                    return (node.id.value, result.success, result.stdout, result.stderr)
                except Exception as exc:  # noqa: BLE001
                    return (node.id.value, False, "", str(exc))

        exec_results: list[tuple[str, bool, str, str]] = list(
            await asyncio.gather(*[_run_one(n) for n in nodes])
        )

        # ── 4. Persist NodeResults + update Workflow ──────────────────────
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
                if wf:
                    wf.update_node_state(node_id, node_status)
            if wf:
                if all_ok:
                    wf.complete()
                else:
                    wf.fail()
                await uow.workflows.save(wf)
            await uow.commit()

        # ── 5. Publish events ─────────────────────────────────────────────
        domain_events: list[DomainEvent] = []
        for node_id_str, ok, _, reason in exec_results:
            node_id = NodeId(node_id_str)
            if ok:
                domain_events.append(
                    NodeCompleted.now(node_id, workflow_id, node_result_ids[node_id_str])
                )
            else:
                domain_events.append(NodeFailed.now(node_id, workflow_id, reason))
        if all_ok:
            domain_events.append(WorkflowCompleted.now(workflow_id, cmd.task_name))
        else:
            domain_events.append(WorkflowFailed.now(workflow_id, cmd.task_name))
        await self._events.publish(domain_events)

        return workflow_id.value
