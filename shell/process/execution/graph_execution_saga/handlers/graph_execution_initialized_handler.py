from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.execution.commands.create_graph_node_execution_command import (
    CreateGraphNodeExecutionCommand,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.events.graph_execution_initialized_event import (
        GraphExecutionInitializedEvent,
    )
    from shell.domain.platform.ports.log import Logger
    from shell.process.execution.graph_execution_saga.graph_execution_saga import (
        GraphExecutionSaga,
    )
    from shell.process.execution.graph_execution_saga.ports.command_publisher import (
        CommandPublisher,
    )


class GraphExecutionInitializedHandler:
    def __init__(
        self,
        saga_manager: GraphExecutionSaga,
        command_publisher: CommandPublisher,
        logger: Logger,
    ) -> None:
        self._saga_manager = saga_manager
        self._command_publisher = command_publisher
        self._logger = logger

    async def handle(self, event: GraphExecutionInitializedEvent) -> None:
        saga = await self._saga_manager.create_saga(
            graph_execution_id=event.graph_execution_id.value,
            expected_nodes_count=len(event.graph_node_definition_ids),
        )

        for node_def_id in event.graph_node_definition_ids:
            command = CreateGraphNodeExecutionCommand(
                graph_execution_id=event.graph_execution_id.value,
                graph_node_definition_id=node_def_id.value,
            )
            await self._command_publisher.publish(
                command_type="CreateGraphNodeExecutionCommand",
                payload={
                    "graph_execution_id": command.graph_execution_id,
                    "graph_node_definition_id": command.graph_node_definition_id,
                },
                occurred_at=event.occurred_at,
            )

        self._logger.info(
            "graph_execution_initialized_handler.saga_created",
            saga_id=saga.saga_id,
            graph_execution_id=event.graph_execution_id.value,
            node_count=len(event.graph_node_definition_ids),
        )
