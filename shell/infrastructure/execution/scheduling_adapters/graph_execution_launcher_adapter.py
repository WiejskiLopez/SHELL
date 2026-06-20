from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork


class GraphExecutionLauncherAdapter:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        logger: Logger,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._logger = logger

    async def launch(
        self,
        *,
        graph_definition_id: str,
        input_state: dict,
        correlation_id: str,
    ) -> str:
        from shell.domain.definition.value_objects.ids import GraphDefinitionId
        from shell.domain.execution.aggregates.graph_execution import (
            GraphExecution,
        )
        from shell.domain.execution.aggregates.workflow import Workflow
        from shell.domain.execution.value_objects.workflow_execution_context import (
            WorkflowExecutionContext,
        )

        now = self._clock.now()

        async with self._uow as uow:
            graph_definition = await uow.graph_definitions.get_by_id(
                GraphDefinitionId(graph_definition_id)
            )
            if graph_definition is None:
                raise ValueError(
                    f"GraphDefinition {graph_definition_id!r} not found"
                )

            child_workflow = Workflow.new(
                id_=self._id_gen.new_workflow_id(),
                now=now,
            )

            graph_execution = GraphExecution.from_graph_definition(
                id_=self._id_gen.new_graph_execution_id(),
                task_execution_id=self._id_gen.new_task_execution_id(),
                graph_definition=graph_definition,
                id_gen=self._id_gen,
                now=now,
                state_input=input_state,
                correlation_id=correlation_id,
                workflow_id=child_workflow.id,
            )

            from shell.domain.execution.services.graph_node_execution_navigator import (
                TransitionBasedNavigator,
            )

            navigator = TransitionBasedNavigator()
            first_node = navigator.first(graph_execution)

            if first_node is not None:
                child_workflow.start_at(
                    first_graph_node_execution_id=first_node.id,
                    context=WorkflowExecutionContext(correlation_id=correlation_id),
                    now=now,
                    task_execution_id=graph_execution.task_execution_id,
                )

            await uow.graph_executions.save(graph_execution)
            await uow.workflows.save(child_workflow)

            events = list(graph_execution.pull_events())
            events.extend(child_workflow.pull_events())

            if first_node is not None:
                from shell.domain.execution.events import (
                    GraphNodeExecutionRequestedEvent,
                )

                child_workflow.append_event(
                    GraphNodeExecutionRequestedEvent.now(
                        workflow_id=child_workflow.id,
                        graph_node_execution_id=first_node.id,
                        now=now,
                    )
                )
                events.extend(child_workflow.pull_events())

            uow.stage_events(events)

            await uow.commit()

            self._logger.info(
                "graph_execution_launcher_adapter.launched",
                graph_execution_id=graph_execution.id.value,
                graph_definition_id=graph_definition_id,
            )

            return graph_execution.id.value
