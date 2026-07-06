from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from shell.application.execution.edge_link_execution.commands.create_edge_link_execution_command import (
    CreateEdgeLinkExecutionCommand,
)
from shell.application.execution.edge_link_execution.commands.delete_edge_link_execution_command import (
    DeleteEdgeLinkExecutionCommand,
)
from shell.domain.execution.aggregates.edge_link_execution.exceptions.edge_link_execution_not_found_error import (
    EdgeLinkExecutionNotFoundError,
)
from shell.framework.execution.edge_link_execution.api.edge_link_execution_response import (
    EdgeLinkExecutionResponse,
)

if TYPE_CHECKING:
    from shell.application.platform.bus.command_bus import CommandBus
    from shell.framework.execution.edge_link_execution.api.create_edge_link_execution_request import (
        CreateEdgeLinkExecutionRequest,
    )


class EdgeLinkExecutionController:
    __slots__ = ("_command_bus",)

    def __init__(self, command_bus: CommandBus) -> None:
        self._command_bus = command_bus

    async def create_edge_link_execution(
        self, body: CreateEdgeLinkExecutionRequest
    ) -> EdgeLinkExecutionResponse:
        command = CreateEdgeLinkExecutionCommand(
            node_execution_id=body.node_execution_id,
            edge_execution_id=body.edge_execution_id,
        )
        try:
            link_id = await self._command_bus.dispatch(command)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return EdgeLinkExecutionResponse(id=str(link_id))

    async def delete_edge_link_execution(self, link_id: str) -> None:
        command = DeleteEdgeLinkExecutionCommand(id=link_id)
        try:
            await self._command_bus.dispatch(command)
        except EdgeLinkExecutionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
