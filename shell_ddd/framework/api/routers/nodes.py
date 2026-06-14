"""Nodes router — query node execution results."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from shell_ddd.application.queries.queries import GetNodeResultQuery

router = APIRouter(prefix="/nodes", tags=["nodes"])


from typing import TYPE_CHECKING

from fastapi import Request as _Request

if TYPE_CHECKING:
    from shell_ddd.bootstrap.container.core_container import CoreContainer


def get_core_container(request: _Request) -> CoreContainer:
    return request.app.state.core_container


@router.get("/{node_id}/result")
async def get_node_result(
    node_id: str,
    workflow_id: str,
        core_container: CoreContainer = Depends(get_core_container),
) -> dict:  # type: ignore[type-arg]
    result = await core_container.app.buses.query_bus().dispatch(GetNodeResultQuery(node_id=node_id, workflow_id=workflow_id))
    if result is None:
        raise HTTPException(status_code=404, detail=f"NodeResult for '{node_id}' not found")
    return {"node_id": node_id, "result": str(result)}
