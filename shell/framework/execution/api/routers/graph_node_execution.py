"""Nodes router — query node execution results."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Request as _Request
from shell.application.platform.queries.queries import GetGraphNodeExecutionResultQuery

if TYPE_CHECKING:
    from shell.application.platform.bus.query_bus import QueryBus
    from shell.bootstrap.platform.container.core_container import CoreContainer
    # Dopasuj ścieżkę importu QueryBus do struktury swojego projektu:

router = APIRouter(prefix="/nodes", tags=["nodes"])


# ------------------------------------------------------------------
# FastAPI Dependencies (Inversion of Control)
# ------------------------------------------------------------------


def get_core_container(request: _Request) -> CoreContainer:
    return request.app.state.core_container


def get_query_bus(container: CoreContainer = Depends(get_core_container)) -> QueryBus:
    """Ekstrahuje QueryBus i izoluje dynamiczne typowanie na granicy infrastruktury."""
    return container.app.buses.query_bus()  # type: ignore[attr-defined]


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@router.get("/{graph_node_execution_id}/result")
async def get_graph_node_execution_result(
    graph_node_execution_id: str,
    workflow_id: str,
    query_bus: QueryBus = Depends(get_query_bus),  # Wstrzyknięty czysty konkret
) -> dict:
    result = await query_bus.dispatch(
        GetGraphNodeExecutionResultQuery(
            graph_node_execution_id=graph_node_execution_id, workflow_id=workflow_id
        )
    )
    if result is None:
        raise HTTPException(
            status_code=404, detail=f"NodeResult for '{graph_node_execution_id}' not found"
        )
    return {"node_execution_id": graph_node_execution_id, "result": str(result)}
