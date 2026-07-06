from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from shell.application.execution.edge_execution.commands.create_edge_execution_command import (
    CreateEdgeExecutionCommand,
)
from shell.application.execution.edge_execution.commands.delete_edge_execution_command import (
    DeleteEdgeExecutionCommand,
)
from shell.application.execution.edge_execution.commands.update_edge_execution_command import (
    UpdateEdgeExecutionCommand,
)
from shell.domain.execution.aggregates.edge_execution.exceptions.edge_execution_not_found_error import (
    EdgeExecutionNotFoundError,
)
from shell.framework.execution.edge_execution.api.edge_execution_response import (
    EdgeExecutionResponse,
)

if TYPE_CHECKING:
    from shell.application.platform.bus.command_bus import CommandBus
    from shell.framework.execution.edge_execution.api.create_edge_execution_request import (
        CreateEdgeExecutionRequest,
    )
    from shell.framework.execution.edge_execution.api.update_edge_execution_request import (
        UpdateEdgeExecutionRequest,
    )


class EdgeExecutionController:
    __slots__ = ("_command_bus",)

    def __init__(self, command_bus: CommandBus) -> None:
        self._command_bus = command_bus

    async def create_edge_execution(
        self, body: CreateEdgeExecutionRequest
    ) -> EdgeExecutionResponse:
        command = CreateEdgeExecutionCommand(
            edge_definition_id=body.edge_definition_id,
            source_node_execution_id=body.source_node_execution_id,
            target_node_execution_id=body.target_node_execution_id,
        )
        try:
            edge_execution_id = await self._command_bus.dispatch(command)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return EdgeExecutionResponse(id=str(edge_execution_id))

    async def update_edge_execution(
        self, edge_execution_id: str, body: UpdateEdgeExecutionRequest
    ) -> None:
        command = UpdateEdgeExecutionCommand(
            id=edge_execution_id,
            target_node_execution_id=body.target_node_execution_id,
        )
        try:
            await self._command_bus.dispatch(command)
        except EdgeExecutionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    async def delete_edge_execution(self, edge_execution_id: str) -> None:
        command = DeleteEdgeExecutionCommand(id=edge_execution_id)
        try:
            await self._command_bus.dispatch(command)
        except EdgeExecutionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
