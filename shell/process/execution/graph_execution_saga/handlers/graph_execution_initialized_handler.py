from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.execution.commands.create_graph_node_execution_command import (
    CreateGraphNodeExecutionCommand,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.events.graph_execution_initialized_event import (
        GraphExecutionInitializedEvent,
    )
    from shell.domain.execution.aggregates.graph_execution.ports.graph_execution_definition_provider import (
        GraphExecutionDefinitionProvider,
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
        definition_provider: GraphExecutionDefinitionProvider,
    ) -> None:
        self._saga_manager = saga_manager
        self._command_publisher = command_publisher
        self._logger = logger
        self._definition_provider = definition_provider

    async def handle(self, event: GraphExecutionInitializedEvent) -> None:
        saga = await self._saga_manager.create_saga(
            graph_execution_id=event.graph_execution_id.value,
            expected_nodes_count=len(event.graph_node_definition_ids),
        )

        definition = await self._definition_provider.get_graph_definition(
            event.graph_definition_id.value,
        )

        for i, node_def_id in enumerate(event.graph_node_definition_ids):
            if definition is None or i >= len(definition.graph_node_execution_definitions):
                self._logger.error(
                    "graph_execution_initialized_handler.definition_missing",
                    node_index=i,
                    definition_id=event.graph_definition_id.value,
                )
                continue

            ndef = definition.graph_node_execution_definitions[i]
            command = CreateGraphNodeExecutionCommand(
                graph_execution_id=event.graph_execution_id.value,
                graph_node_definition_id=node_def_id.value,
                position=ndef.position,
                role=ndef.role,
                mode=ndef.mode,
                node_type=ndef.node_type,
                remaining_retries=ndef.retries,
                timeout_seconds=ndef.timeout,
            )
            await self._command_publisher.publish(
                command_type="CreateGraphNodeExecutionCommand",
                payload={
                    "graph_execution_id": command.graph_execution_id,
                    "graph_node_definition_id": command.graph_node_definition_id,
                    "position": command.position,
                    "role": command.role,
                    "mode": command.mode,
                    "node_type": command.node_type,
                    "remaining_retries": command.remaining_retries,
                    "timeout_seconds": command.timeout_seconds,
                },
                occurred_at=event.occurred_at.value,
            )

        self._logger.info(
            "graph_execution_initialized_handler.saga_created",
            saga_id=saga.saga_id,
            graph_execution_id=event.graph_execution_id.value,
            node_count=len(event.graph_node_definition_ids),
        )
