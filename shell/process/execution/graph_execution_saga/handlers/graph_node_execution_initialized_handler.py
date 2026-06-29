from __future__ import annotations

from typing import TYPE_CHECKING

from shell.process.execution.graph_execution_saga.state import (
    GraphExecutionSagaStatus,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_initialized_event import (
        GraphNodeExecutionInitializedEvent,
    )
    from shell.domain.platform.ports.log import Logger
    from shell.process.execution.graph_execution_saga.graph_execution_saga import (
        GraphExecutionSaga,
    )
    from shell.process.execution.graph_execution_saga.ports.command_publisher import (
        CommandPublisher,
    )


class GraphNodeExecutionInitializedHandler:
    def __init__(
        self,
        saga_manager: GraphExecutionSaga,
        command_publisher: CommandPublisher,
        logger: Logger,
    ) -> None:
        self._saga_manager = saga_manager
        self._command_publisher = command_publisher
        self._logger = logger

    async def handle(self, event: GraphNodeExecutionInitializedEvent) -> None:
        saga = await self._saga_manager.record_node_execution(
            graph_execution_id=event.graph_execution_id.value,
            node_definition_id=event.node_definition_id.value,
            node_execution_id=event.node_id.value,
        )

        if saga is None or saga.status != GraphExecutionSagaStatus.COMPLETED:
            return

        await self._command_publisher.publish(
            command_type="AttachGraphNodeExecutionsCommand",
            payload={
                "graph_execution_id": saga.graph_execution_id,
                "graph_node_definition_executions": saga.graph_node_definition_executions,
            },
            occurred_at=event.occurred_at.value,
        )

        self._logger.info(
            "graph_node_execution_initialized_handler.saga_completed",
            saga_id=saga.saga_id,
            graph_execution_id=event.graph_execution_id.value,
        )
