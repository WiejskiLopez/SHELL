"""NodeExecutionCompletedHandler — decides next step after a node result.

This handler subscribes to :class:`NodeExecutionCompletedEvent` and
:class:`NodeExecutionFailedEvent` on the in-process EventBus.  Each
invocation processes **exactly one** result and decides the next
workflow transition:

* advance to the next node (via :class:`NodeExecutionNavigator`)
* fan out to parallel nodes
* evaluate conditional branches
* route to error handler on failure
* finish the workflow (terminal: ``done``)
* abort the workflow (terminal: ``failed``)

This is **Cycle B** of the node-execution saga.
Sub-graph spawning is now handled by PLANNER nodes via CrownScheduler.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.aggregates.node_execution.repositories.node_execution_repository import (
    NodeExecutionRepository,
)
from shell.domain.execution.aggregates.node_transition_execution.repositories.node_transition_execution_repository import (
    NodeTransitionExecutionRepository,
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
    NodeExecutionNavigator,
    LinearNodeExecutionNavigator,
)
from shell.domain.execution.services.node_execution_policy import (
    AbortDecision,
    ContinueDecision,
    FailFastNodeExecutionPolicy,
    NodeExecutionPolicy,
)
from shell.domain.execution.value_objects.edge_type import EdgeType
from shell.domain.execution.value_objects.workflow_status import WorkflowStatus
from shell.domain.platform.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from datetime import datetime

    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.aggregates.node_transition_execution.node_transition_execution import (
        NodeTransitionExecution,
    )
    from shell.domain.execution.aggregates.workflow import Workflow
    from shell.domain.execution.value_objects.ids import NodeExecutionId
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock

NodeExecutionResultEvent = NodeExecutionCompletedEvent | NodeExecutionFailedEvent


class NodeExecutionCompletedHandler:
    """Cycle B: decides next step after receiving a node execution result.

    Supports SEQUENCE, PARALLEL, CONDITIONAL, LOOP, ERROR_HANDLER, and
    DEFAULT transition types through the ``NodeExecutionNavigator``.

    Sub-graph spawning is now handled by PLANNER nodes via CrownScheduler.
    """

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
            workflow_id = node_execution_result_event.workflow_id
            if workflow_id is None:
                self._logger.warning(
                    "node_execution_completed_handler.workflow_id_missing",
                )
                return

            workflow = await unit_of_work.repository(WorkflowRepository).get_by_id(workflow_id)
            if workflow is None:
                self._logger.warning(
                    "node_execution_completed_handler.workflow_not_found",
                    workflow_id=workflow_id.value,
                )
                return

            if workflow.status != WorkflowStatus.ACTIVE:
                self._logger.warning(
                    "node_execution_completed_handler.skip_workflow_not_active",
                    workflow_id=workflow_id.value,
                    status=workflow.status.value,
                )
                return

            graph_executions = await unit_of_work.repository(
                GraphExecutionRepository
            ).get_by_workflow_id(workflow.id)
            if not graph_executions:
                self._logger.warning(
                    "node_execution_completed_handler.no_graph",
                    workflow_id=workflow.id.value,
                )
                return
            graph_execution = graph_executions[0]

            now = self._clock.now()

            if isinstance(node_execution_result_event, NodeExecutionCompletedEvent):
                await self._handle_completed(
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
                    reason=node_execution_result_event.reason,
                    now=now,
                    unit_of_work=unit_of_work,
                )

            await unit_of_work.repository(WorkflowRepository).save(workflow)
            unit_of_work.stage_events(workflow.pull_events())

    # ── Private helpers ───────────────────────────────────────────────────

    async def _handle_completed(
        self,
        *,
        workflow: Workflow,
        graph_execution: GraphExecution,
        node_execution_id: NodeExecutionId,
        now: datetime,
        unit_of_work: UnitOfWork,
    ) -> None:
        transition_repo = unit_of_work.repository(NodeTransitionExecutionRepository)
        outgoing = await transition_repo.list_outgoing_for_node(node_execution_id)
        if not outgoing:
            await self._advance_or_finish(
                workflow=workflow,
                graph_execution=graph_execution,
                node_execution_id=node_execution_id,
                now=now,
                unit_of_work=unit_of_work,
            )
            return

        transition_types = {t.edge_type for t in outgoing}

        if EdgeType.LOOP in transition_types:
            await self._handle_loop(
                workflow=workflow,
                graph_execution=graph_execution,
                node_execution_id=node_execution_id,
                now=now,
                outgoing=list(outgoing),
                unit_of_work=unit_of_work,
            )
            return

        await self._advance_or_finish(
            workflow=workflow,
            graph_execution=graph_execution,
            node_execution_id=node_execution_id,
            now=now,
            unit_of_work=unit_of_work,
        )

    async def _handle_loop(
        self,
        *,
        workflow: Workflow,
        graph_execution: GraphExecution,
        node_execution_id: NodeExecutionId,
        now: datetime,
        outgoing: list[NodeTransitionExecution],
        unit_of_work: UnitOfWork,
    ) -> None:
        loop_transition = None
        for t in outgoing:
            if t.edge_type == EdgeType.LOOP:
                loop_transition = t
                break

        if (
            loop_transition is None
            or loop_transition.max_iterations.value is None
            or loop_transition.max_iterations.value <= 0
        ):
            await self._advance_or_finish(
                workflow=workflow,
                graph_execution=graph_execution,
                node_execution_id=node_execution_id,
                now=now,
                unit_of_work=unit_of_work,
            )
            return

        target_node_id = loop_transition.target_node_execution_id
        if target_node_id is None:
            await self._advance_or_finish(
                workflow=workflow,
                graph_execution=graph_execution,
                node_execution_id=node_execution_id,
                now=now,
                unit_of_work=unit_of_work,
            )
            return

        unit_of_work.stage_events(
            [
                NodeExecutionAdvancedEvent.now(
                    workflow.id,
                    node_execution_id,
                    target_node_id,
                    CreatedAt.from_datetime(now),
                ),
                NodeExecutionRequestedEvent.now(
                    workflow.id, target_node_id, CreatedAt.from_datetime(now)
                ),
            ]
        )

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
                unit_of_work.repository(NodeTransitionExecutionRepository),
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

        error_handler_node = await self._find_error_handler_transition(
            graph_execution,
            node_execution_id,
            unit_of_work.repository(NodeTransitionExecutionRepository),
        )

        if error_handler_node is not None:
            unit_of_work.stage_events(
                [
                    NodeExecutionAdvancedEvent.now(
                        workflow.id,
                        node_execution_id,
                        error_handler_node,
                        CreatedAt.from_datetime(now),
                    ),
                    NodeExecutionRequestedEvent.now(
                        workflow.id, error_handler_node, CreatedAt.from_datetime(now)
                    ),
                ]
            )
            return

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

    @staticmethod
    async def _find_error_handler_transition(
        graph_execution: GraphExecution,
        node_execution_id: NodeExecutionId,
        transition_repo: NodeTransitionExecutionRepository,
    ) -> NodeExecutionId | None:
        outgoing = await transition_repo.list_outgoing_for_node(node_execution_id)
        for t in outgoing:
            if t.edge_type == EdgeType.ERROR_HANDLER and t.target_node_execution_id is not None:
                return t.target_node_execution_id
        return None
