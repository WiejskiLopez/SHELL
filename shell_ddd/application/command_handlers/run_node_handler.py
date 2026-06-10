"""RunNodeHandler — executes a node within a workflow using the appropriate strategy."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.entities.node_result import NodeResult
from shell_ddd.domain.events.events import NodeCompleted, NodeFailed
from shell_ddd.domain.exceptions import WorkflowNotFound
from shell_ddd.domain.value_objects.ids import NodeId, WorkflowId
from shell_ddd.domain.value_objects.status import Status

if TYPE_CHECKING:
    from shell_ddd.application.commands.commands import RunNodeCommand
    from shell_ddd.application.ports.ports import (
        Clock,
        EventPublisher,
        IdGenerator,
        NodeProcessRunner,
        NodeWorkspace,
        UnitOfWork,
    )
    from shell_ddd.application.strategies.node_execution_strategy import NodeExecutionStrategy


class RunNodeHandler:
    """Executes a graph node via the registered NodeExecutionStrategy for its mode.

    Saves a NodeResult, updates Workflow.node_states, and publishes NodeCompleted/NodeFailed.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        workspace: NodeWorkspace,
        runner: NodeProcessRunner,
        strategy: NodeExecutionStrategy,
        event_publisher: EventPublisher,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._workspace = workspace
        self._runner = runner
        self._strategy = strategy
        self._event_publisher = event_publisher

    async def handle(self, cmd: RunNodeCommand) -> str:
        """Execute node and return NodeResult id."""
        wf_id = WorkflowId(cmd.workflow_id)
        node_id = NodeId(cmd.node_id)
        now = self._clock.now()

        async with self._uow as uow:
            workflow = await uow.workflows.get_by_id(wf_id)
            if workflow is None:
                raise WorkflowNotFound(cmd.workflow_id)

            workflow.update_node_state(node_id, Status.running(), now=now)
            await uow.workflows.save(workflow)
            await uow.commit()

        # Execute strategy (outside UoW — may take a long time)
        try:
            result = await self._strategy.execute(
                node_id=cmd.node_id,
                workspace_path=cmd.workspace_path,
                runner=self._runner,
            )
            node_status = Status.done()
        except Exception as exc:
            # Capture failure without re-raising so we can persist result
            result_status = Status.failed()
            node_result_id = self._id_gen.new_node_result_id()
            node_result = NodeResult.new(
                id_=node_result_id,
                node_id=node_id,
                workflow_id=wf_id,
                status=result_status,
                stderr=str(exc),
                now=now,
            )
            async with self._uow as uow:
                await uow.node_results.save(node_result)
                wf = await uow.workflows.get_by_id(wf_id)
                if wf:
                    wf.update_node_state(node_id, result_status, now=now)
                    await uow.workflows.save(wf)
                uow.stage_events([NodeFailed.now(node_id, wf_id, str(exc), now=now)])
                await uow.commit()
            await self._event_publisher.publish(uow.events)
            return node_result_id.value

        node_result_id = self._id_gen.new_node_result_id()
        node_result = NodeResult.new(
            id_=node_result_id,
            node_id=node_id,
            workflow_id=wf_id,
            status=node_status,
            stdout=result.stdout,
            stderr=result.stderr,
            artifact_uri="",
            now=now,
        )

        async with self._uow as uow:
            await uow.node_results.save(node_result)
            wf = await uow.workflows.get_by_id(wf_id)
            if wf:
                wf.update_node_state(node_id, node_status, now=now)
                await uow.workflows.save(wf)
            uow.stage_events([NodeCompleted.now(node_id, wf_id, node_result_id, now=now)])
            await uow.commit()

        await self._event_publisher.publish(uow.events)
        return node_result_id.value
