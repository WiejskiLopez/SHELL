from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.events.sub_graph_settled_event import (
    SubGraphSettledEvent,
)

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork


class HandleSubGraphSettled:
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

    async def handle(self, event: SubGraphSettledEvent) -> None:
        async with self._uow as uow:
            parent_graph = await uow.graph_executions.get_by_id(
                event.parent_graph_execution_id,
            )
            if parent_graph is None:
                self._logger.warning(
                    "handle_sub_graph_settled.parent_not_found",
                    parent_graph_execution_id=event.parent_graph_execution_id.value,
                )
                return

            now = self._clock.now()
            parent_graph.absorb_child_results(event.child_results, now)
            await uow.graph_executions.save(parent_graph)
            uow.stage_events(parent_graph.pull_events())
