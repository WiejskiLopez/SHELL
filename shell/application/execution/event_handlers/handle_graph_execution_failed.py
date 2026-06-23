from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_failed_event import (
    GraphExecutionFailedEvent,
)

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork


class HandleGraphExecutionFailed:
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

    async def handle(self, event: GraphExecutionFailedEvent) -> None:
        async with self._uow as uow:
            graph_execution = await uow.graph_executions.get_by_id(event.graph_execution_id)
            if graph_execution is None:
                self._logger.warning(
                    "handle_graph_execution_failed.graph_not_found",
                    graph_execution_id=event.graph_execution_id.value,
                )
                return

            if graph_execution.parent_graph_execution_id is not None:
                return

            task_execution = await uow.task_executions.get_by_id(
                graph_execution.task_execution_id,
            )
            if task_execution is None:
                self._logger.warning(
                    "handle_graph_execution_failed.task_not_found",
                    task_execution_id=graph_execution.task_execution_id.value,
                )
                return

            now = self._clock.now()
            can_continue = task_execution.increment_cycle()
            if not can_continue:
                task_execution.exhaust(now)
                await uow.task_executions.save(task_execution)
                uow.stage_events(task_execution.pull_events())
                return

            replan_goal = f"replan: {graph_execution.task_execution_id.value} - {event.reason}"
            new_graph = GraphExecution.create_main_round(
                id_=self._id_gen.new_graph_execution_id(),
                task_execution_id=graph_execution.task_execution_id,
            )
            from shell.domain.execution.aggregates.graph_execution.events.graph_execution_created_event import (
                GraphExecutionCreatedEvent,
            )

            new_graph.append_event(
                GraphExecutionCreatedEvent.now(
                    graph_execution_id=new_graph.id,
                    task_execution_id=graph_execution.task_execution_id,
                    now=now,
                    goal=replan_goal,
                    depth=0,
                ),
            )
            await uow.graph_executions.save(new_graph)
            await uow.task_executions.save(task_execution)
            uow.stage_events(new_graph.pull_events())
            uow.stage_events(task_execution.pull_events())
