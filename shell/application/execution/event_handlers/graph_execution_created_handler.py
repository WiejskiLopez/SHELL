"""GraphExecutionCreatedHandler — loguje utworzenie GraphExecution.

Nie modyfikuje żadnego agregatu. TaskExecution jest uruchamiany przez
``GraphExecutionCreatedTaskExecutionCycleHandler``, a stan tworzony przez
``GraphExecutionCreatedGoalStateHandler``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)

if TYPE_CHECKING:
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.graph_execution.events.event import (
        GraphExecutionCreatedEvent,
    )
    from shell.domain.platform.ports.log import Logger


class GraphExecutionCreatedHandler:
    """Rejestruje utworzenie GraphExecution, nie modyfikuje agregatów."""

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        logger: Logger,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._logger = logger

    async def handle(self, event: GraphExecutionCreatedEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            graph_execution = await unit_of_work.repository(GraphExecutionRepository).get_by_id(
                event.graph_execution_id
            )
            if graph_execution is None:
                self._logger.warning(
                    "graph_execution_created_handler.graph_execution_not_found",
                    graph_execution_id=event.graph_execution_id.value,
                )
                return

        self._logger.info(
            "graph_execution_created_handler.created",
            graph_execution_id=event.graph_execution_id.value,
            task_execution_id=graph_execution.task_execution_id.value,
            parent_id=(
                graph_execution.parent_graph_execution_id.value
                if graph_execution.parent_graph_execution_id
                else None
            ),
        )
