"""Nodes router — query node execution results."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from shell_ddd.application.queries.queries import GetNodeResultQuery
from shell_ddd.bootstrap.container import Container

router = APIRouter(prefix="/nodes", tags=["nodes"])


from fastapi import Request as _Request


def get_container(request: _Request) -> Container:
    return request.app.state.container


@router.get("/{node_id}/result")
async def get_node_result(
    node_id: str,
    workflow_id: str,
    container: Container = Depends(get_container),
) -> dict:  # type: ignore[type-arg]
    result = await container.query_bus.dispatch(GetNodeResultQuery(node_id=node_id, workflow_id=workflow_id))
    if result is None:
        raise HTTPException(status_code=404, detail=f"NodeResult for '{node_id}' not found")
    return {"node_id": node_id, "result": str(result)}
