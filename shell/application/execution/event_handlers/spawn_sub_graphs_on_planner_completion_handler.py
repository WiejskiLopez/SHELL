"""PlannerResultHandler — processes PLANNER node output and spawns sub-graphs.

Subscribes to GraphNodeExecutionCompletedEvent for PLANNER-mode nodes.
Parses the planner's JSON output and:
1. Spawns sub-graphs for each plan step
2. Registers children with CrownScheduler
3. Marks the workflow as waiting for children
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from shell.domain.execution.events import GraphNodeExecutionCompletedEvent
from shell.domain.platform.value_objects.mode import Mode

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.aggregates.workflow import Workflow
    from shell.domain.execution.entities.graph_node_execution import GraphNodeExecution
    from shell.domain.execution.ports.crown_scheduler import CrownScheduler
    from shell.domain.execution.services.sub_graph_execution_service import (
        SubGraphExecutionService,
    )
    from shell.domain.execution.value_objects.ids import GraphNodeExecutionId


class SpawnSubGraphsOnPlannerCompletionHandler:
    """Processes PLANNER node output and spawns sub-graphs via CrownScheduler."""

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        logger: Logger,
        sub_graph_service: SubGraphExecutionService,
        crown_scheduler: CrownScheduler,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._logger = logger
        self._sub_graph_service = sub_graph_service
        self._crown_scheduler = crown_scheduler

    async def handle(self, event: GraphNodeExecutionCompletedEvent) -> None:
        """Handle PLANNER node completion — parse plan and spawn sub-graphs."""
        async with self._uow as uow:
            workflow = await uow.workflows.get_by_id(event.workflow_id)
            if workflow is None or workflow.status.value not in ("running", "idle"):
                return

            graph_executions = await uow.graph_executions.get_by_workflow_id(
                workflow.id,
            )
            if not graph_executions:
                return
            graph_execution = graph_executions[0]

            node = self._find_node(graph_execution, event.graph_node_execution_id)
            if node is None or node.mode != Mode.PLANNER:
                return

            result = workflow.get_graph_node_execution_result(
                event.graph_node_execution_id,
            )
            if result is None or not result.stdout:
                return

            plan = self._parse_plan(result.stdout)
            if plan is None or not plan.get("steps"):
                return

            now = self._clock.now()
            child_graph_ids: list[str] = []
            correlation_id = workflow.execution_context.correlation_id

            for step in plan["steps"]:
                action = step.get("action")
                if action == "spawn_sub_graph":
                    child = await self._spawn_sub_graph(
                        graph_execution=graph_execution,
                        node=node,
                        step=step,
                        correlation_id=correlation_id,
                        uow=uow,
                    )
                    if child is not None:
                        child_graph_ids.append(child.id.value)

            if child_graph_ids:
                workflow.wait_for_children(
                    graph_node_execution_id=event.graph_node_execution_id,
                    now=now,
                )
                try:
                    await uow.workflows.save(workflow)
                except WorkflowConcurrentlyModified:
                    self._logger.warning(
                        "spawn_sub_graphs_on_planner_completion_handler.concurrent_modification",
                        workflow_id=workflow.id.value,
                    )
                    return
                uow.stage_events(workflow.pull_events())

                # Register children + mark waiting after successful save
                for child_id in child_graph_ids:
                    from shell.domain.execution.value_objects.ids import GraphExecutionId
                    await self._crown_scheduler.register_child(
                        parent_graph_execution_id=graph_execution.id,
                        child_graph_execution_id=GraphExecutionId(child_id),
                    )
                await self._crown_scheduler.mark_waiting(graph_execution.id)

                self._logger.info(
                    "spawn_sub_graphs_on_planner_completion_handler.waiting_for_children",
                    planner_node_id=event.graph_node_execution_id.value,
                    child_count=len(child_graph_ids),
                )

    async def _spawn_sub_graph(
        self,
        *,
        graph_execution: GraphExecution,
        node: GraphNodeExecution,
        step: dict[str, Any],
        correlation_id: str,
        uow: UnitOfWork,
    ) -> GraphExecution | None:
        from shell.domain.definition.value_objects.ids import GraphDefinitionId

        sub_graph_def_id = step.get("sub_graph_definition_id")
        if not sub_graph_def_id:
            self._logger.warning(
                "spawn_sub_graphs_on_planner_completion_handler.missing_definition_id",
                step=str(step),
            )
            return None

        try:
            state_input = step.get("state_input", {})
            child = await self._sub_graph_service.spawn(
                parent_graph_execution=graph_execution,
                parent_tasker_node=node,
                graph_definition_id=GraphDefinitionId(sub_graph_def_id),
                state_input=state_input,
                correlation_id=correlation_id,
                uow=uow,
            )
            return child
        except Exception as exc:
            self._logger.error(
                "spawn_sub_graphs_on_planner_completion_handler.spawn_failed",
                definition_id=sub_graph_def_id,
                error=str(exc),
            )
            return None

    @staticmethod
    def _parse_plan(stdout: str) -> dict[str, Any] | None:
        """Parse planner output JSON."""
        try:
            return json.loads(stdout)
        except (json.JSONDecodeError, ValueError):
            return None

    @staticmethod
    def _find_node(
        graph_execution: GraphExecution,
        node_id: GraphNodeExecutionId,
    ) -> GraphNodeExecution | None:
        for node in graph_execution.graph_node_executions:
            if node.id == node_id:
                return node
        return None
