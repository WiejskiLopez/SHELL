from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from shell.execution.application.execution.edge_execution.commands.create_edge_execution_command import (
    CreateEdgeExecutionCommand,
)
from shell.execution.application.execution.edge_execution.commands.delete_edge_execution_command import (
    DeleteEdgeExecutionCommand,
)
from shell.execution.application.execution.edge_execution.commands.update_edge_execution_command import (
    UpdateEdgeExecutionCommand,
)
from shell.execution.application.execution.edge_execution.queries.get_edge_execution_by_id_query import (
    GetEdgeExecutionByIdQuery,
)
from shell.execution.domain.execution.aggregates.edge_execution.exceptions.edge_execution_not_found_error import (
    EdgeExecutionNotFoundError,
)
from shell.execution.framework.execution.edge_execution.api.edge_execution_response import (
    EdgeExecutionResponse,
)

if TYPE_CHECKING:
    from shell.execution.framework.execution.edge_execution.api.create_edge_execution_request import (
        CreateEdgeExecutionRequest,
    )
    from shell.execution.framework.execution.edge_execution.api.update_edge_execution_request import (
        UpdateEdgeExecutionRequest,
    )
    from shell.platform.application.bus.command_bus import CommandBus
    from shell.platform.application.bus.query_bus import QueryBus


class EdgeExecutionController:
    __slots__ = ("_command_bus", "_query_bus")

    def __init__(self, command_bus: CommandBus, query_bus: QueryBus) -> None:
        self._command_bus = command_bus
        self._query_bus = query_bus

    async def get_edge_execution(self, edge_execution_id: str) -> EdgeExecutionResponse:
        result = await self._query_bus.dispatch(
            GetEdgeExecutionByIdQuery(edge_execution_id=edge_execution_id)
        )
        if result is None:
            raise HTTPException(
                status_code=404, detail=f"EdgeExecution '{edge_execution_id}' not found"
            )
        return EdgeExecutionResponse(
            id=result.id,
            edge_definition_id=result.edge_definition_id,
            source_node_execution_id=result.source_node_execution_id,
            target_node_execution_id=result.target_node_execution_id,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )

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
