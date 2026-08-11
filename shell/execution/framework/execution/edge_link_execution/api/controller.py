from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from shell.execution.application.execution.edge_link_execution.commands.create_edge_link_execution_command import (
    CreateEdgeLinkExecutionCommand,
)
from shell.execution.application.execution.edge_link_execution.commands.delete_edge_link_execution_command import (
    DeleteEdgeLinkExecutionCommand,
)
from shell.execution.application.execution.edge_link_execution.queries.get_edge_link_execution_by_id_query import (
    GetEdgeLinkExecutionByIdQuery,
)
from shell.execution.domain.execution.aggregates.edge_link_execution.exceptions.edge_link_execution_not_found_error import (
    EdgeLinkExecutionNotFoundError,
)
from shell.execution.framework.execution.edge_link_execution.api.edge_link_execution_response import (
    EdgeLinkExecutionResponse,
)

if TYPE_CHECKING:
    from shell.execution.framework.execution.edge_link_execution.api.create_edge_link_execution_request import (
        CreateEdgeLinkExecutionRequest,
    )
    from shell.platform.application.bus.command_bus import CommandBus
    from shell.platform.application.bus.query_bus import QueryBus


class EdgeLinkExecutionController:
    __slots__ = ("_command_bus", "_query_bus")

    def __init__(self, command_bus: CommandBus, query_bus: QueryBus) -> None:
        self._command_bus = command_bus
        self._query_bus = query_bus

    async def get_edge_link_execution(self, link_id: str) -> EdgeLinkExecutionResponse:
        result = await self._query_bus.dispatch(
            GetEdgeLinkExecutionByIdQuery(edge_link_execution_id=link_id)
        )
        if result is None:
            raise HTTPException(status_code=404, detail=f"EdgeLinkExecution '{link_id}' not found")
        return EdgeLinkExecutionResponse(
            id=result.id,
            node_execution_id=result.node_execution_id,
            edge_execution_id=result.edge_execution_id,
            created_at=result.created_at,
            updated_at=result.updated_at,
            deleted_at=result.deleted_at,
        )

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
