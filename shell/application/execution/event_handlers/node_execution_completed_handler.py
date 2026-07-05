"""NodeExecutionCompletedHandler — decides next step after a node result.

This handler subscribes to :class:`NodeExecutionCompletedEvent` and
:class:`NodeExecutionFailedEvent` on the in-process EventBus.  Each
invocation processes **exactly one** result and decides the next
workflow transition:

* advance to the next node (via :class:`NodeExecutionNavigator`)
* finish the workflow (terminal: ``done``)
* abort the workflow (terminal: ``failed``)

This is **Cycle B** of the node-execution saga.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.aggregates.node_execution.repositories.node_execution_repository import (
    NodeExecutionRepository,
)
from shell.domain.execution.aggregates.node_link_execution.repositories.node_link_execution_repository import (
    NodeLinkExecutionRepository,
)
from shell.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)
from shell.domain.execution.aggregates.workflow.events.node_execution_advanced_event import (
    NodeExecutionAdvancedEvent,
)
from shell.domain.execution.aggregates.workflow.events.node_execution_requested_event import (
    NodeExecutionRequestedEvent,
)
from shell.domain.execution.aggregates.workflow.repositories.workflow_repository import (
    WorkflowRepository,
)
from shell.domain.execution.events import (
    NodeExecutionCompletedEvent,
    NodeExecutionFailedEvent,
)
from shell.domain.execution.services.node_execution_navigator import (
    LinearNodeExecutionNavigator,
    NodeExecutionNavigator,
)
from shell.domain.execution.services.node_execution_policy import (
    AbortDecision,
    ContinueDecision,
    FailFastNodeExecutionPolicy,
    NodeExecutionPolicy,
)
from shell.domain.execution.value_objects.workflow_status import WorkflowStatus
from shell.domain.platform.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from datetime import datetime

    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.aggregates.workflow import Workflow
    from shell.domain.execution.value_objects.ids import NodeExecutionId
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock

NodeExecutionResultEvent = NodeExecutionCompletedEvent | NodeExecutionFailedEvent


class NodeExecutionCompletedHandler:
    """Cycle B: decides next step after receiving a node execution result."""

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
        logger: Logger,
        navigator: NodeExecutionNavigator | None = None,
        policy: NodeExecutionPolicy | None = None,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator
        self._logger = logger
        self._navigator: NodeExecutionNavigator = (
            navigator or LinearNodeExecutionNavigator()
        )
        self._policy: NodeExecutionPolicy = policy or FailFastNodeExecutionPolicy()

    async def handle(
        self, node_execution_result_event: NodeExecutionResultEvent
    ) -> None:
        """Handle exactly one node execution result."""
        async with self._unit_of_work as unit_of_work:
            node_execution_id = node_execution_result_event.node_execution_id

            links = await unit_of_work.repository(
                NodeLinkExecutionRepository
            ).list_by_node_execution_id(node_execution_id)
            if not links:
                self._logger.warning(
                    "node_execution_completed_handler.no_link",
                    node_id=node_execution_id.value,
                )
                return
            graph_execution = await unit_of_work.repository(
                GraphExecutionRepository
            ).get_by_id(links[0].graph_execution_id)
            if graph_execution is None:
                self._logger.warning(
                    "node_execution_completed_handler.no_graph",
                    node_id=node_execution_id.value,
                )
                return

            task_execution = await unit_of_work.repository(
                TaskExecutionRepository
            ).get_by_id(graph_execution.task_execution_id)
            if task_execution is None or task_execution.workflow_id is None:
                self._logger.warning(
                    "node_execution_completed_handler.task_execution_missing",
                    task_execution_id=graph_execution.task_execution_id.value,
                )
                return

            workflow = await unit_of_work.repository(WorkflowRepository).get_by_id(
                task_execution.workflow_id
            )
            if workflow is None:
                self._logger.warning(
                    "node_execution_completed_handler.workflow_not_found",
                    workflow_id=task_execution.workflow_id.value,
                )
                return

            if workflow.status != WorkflowStatus.ACTIVE:
                self._logger.warning(
                    "node_execution_completed_handler.skip_workflow_not_active",
                    workflow_id=task_execution.workflow_id.value,
                    status=workflow.status.value,
                )
                return

            now = self._clock.now()

            if isinstance(node_execution_result_event, NodeExecutionCompletedEvent):
                await self._advance_or_finish(
                    workflow=workflow,
                    graph_execution=graph_execution,
                    node_execution_id=node_execution_result_event.node_execution_id,
                    now=now,
                    unit_of_work=unit_of_work,
                )
            else:
                await self._handle_failure(
                    workflow=workflow,
                    graph_execution=graph_execution,
                    node_execution_id=node_execution_result_event.node_execution_id,
                    reason=f"Node execution failed: {node_execution_result_event.node_execution_id.value}",
                    now=now,
                    unit_of_work=unit_of_work,
                )

            await unit_of_work.repository(WorkflowRepository).save(workflow)
            unit_of_work.stage_events(workflow.pull_events())

    # ── Private helpers ───────────────────────────────────────────────────

    async def _advance_or_finish(
        self,
        *,
        workflow: Workflow,
        graph_execution: GraphExecution,
        node_execution_id: NodeExecutionId,
        now: datetime,
        unit_of_work: UnitOfWork,
    ) -> None:
        next_nodes = list(
            await self._navigator.next_after_async(
                graph_execution,
                node_execution_id,
                unit_of_work.repository(NodeExecutionRepository),
            )
        )
        if not next_nodes:
            workflow.finish(now, task_execution_id=graph_execution.task_execution_id)
            return
        next_node = next_nodes[0]
        unit_of_work.stage_events(
            [
                NodeExecutionAdvancedEvent.now(
                    workflow.id, node_execution_id, next_node.id, CreatedAt.from_datetime(now)
                ),
                NodeExecutionRequestedEvent.now(
                    workflow.id, next_node.id, CreatedAt.from_datetime(now)
                ),
            ]
        )

    async def _handle_failure(
        self,
        *,
        workflow: Workflow,
        graph_execution: GraphExecution,
        node_execution_id: NodeExecutionId,
        reason: str,
        now: datetime,
        unit_of_work: UnitOfWork,
    ) -> None:
        decision = self._policy.decide_after_failure(workflow, node_execution_id, reason)
        if isinstance(decision, ContinueDecision):
            await self._advance_or_finish(
                workflow=workflow,
                graph_execution=graph_execution,
                node_execution_id=node_execution_id,
                now=now,
                unit_of_work=unit_of_work,
            )
            return

        abort_reason = decision.reason if isinstance(decision, AbortDecision) else reason
        workflow.abort(
            reason=abort_reason,
            now=now,
            task_execution_id=graph_execution.task_execution_id,
        )
