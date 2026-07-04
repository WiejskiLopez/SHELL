from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.execution.commands.create_node_execution_command import (
    CreateNodeExecutionCommand,
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
    from shell.process.execution.graph_execution_saga.ports.graph_definition_node_provider import (
        GraphDefinitionNodeProvider,
    )


class GraphExecutionInitializedHandler:
    def __init__(
        self,
        saga_manager: GraphExecutionSaga,
        command_publisher: CommandPublisher,
        definition_node_provider: GraphDefinitionNodeProvider,
        logger: Logger,
    ) -> None:
        self._saga_manager = saga_manager
        self._command_publisher = command_publisher
        self._definition_node_provider = definition_node_provider
        self._logger = logger

    async def handle(self, event: GraphExecutionInitializedEvent) -> None:
        node_definitions = await self._definition_node_provider.get_node_definitions(
            event.graph_definition_id.value,
        )

        saga = await self._saga_manager.create_saga(
            graph_execution_id=event.graph_execution_id.value,
            expected_nodes_count=len(node_definitions),
        )

        for node_def in node_definitions:
            command = CreateNodeExecutionCommand(
                graph_execution_id=event.graph_execution_id.value,
                node_definition_id=node_def.node_id,
                position=node_def.position,
                role=node_def.role,
                mode=node_def.mode,
                node_type=node_def.node_type,
            )
            await self._command_publisher.publish(
                command_type="CreateNodeExecutionCommand",
                payload={
                    "graph_execution_id": command.graph_execution_id,
                    "node_definition_id": command.node_definition_id,
                    "position": command.position,
                    "role": command.role,
                    "mode": command.mode,
                    "node_type": command.node_type,
                },
                occurred_at=event.occurred_at.value,
            )

        self._logger.info(
            "graph_execution_initialized_handler.saga_created",
            saga_id=saga.saga_id,
            graph_execution_id=event.graph_execution_id.value,
            node_count=len(node_definitions),
        )
